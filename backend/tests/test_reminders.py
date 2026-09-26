"""Varredura de lembretes (`scan_reminders`) e entrega pelo WebSocket."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.db.session import SessionLocal
from app.models.schedule import Schedule
from app.services.scheduler import format_reminder_message, scan_reminders


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _create(client, user, start: datetime, **extra) -> dict:
    response = client.post(
        "/api/schedules",
        json={"title": "Revisão", "start_at": start.isoformat(),
              "end_at": (start + timedelta(hours=1)).isoformat(), **extra},
        headers=user.headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _force_due(schedule_id: int, remind_at: datetime) -> None:
    """Simula a passagem do tempo: o lembrete venceu e ainda não foi enviado."""
    with SessionLocal() as db:
        db.execute(
            update(Schedule)
            .where(Schedule.id == schedule_id)
            .values(remind_at=remind_at, reminder_sent=False)
        )
        db.commit()


def _notifications(client, user) -> dict:
    return client.get("/api/notifications", headers=user.headers).json()


def test_due_reminder_fires_once(client, user):
    session = _create(client, user, _now() + timedelta(minutes=15))
    _force_due(session["id"], _now())

    scan_reminders()
    scan_reminders()

    listing = _notifications(client, user)
    mine = [n for n in listing["items"] if n["schedule_id"] == session["id"]]
    assert len(mine) == 1
    assert mine[0]["title"] == "Lembrete: Revisão"
    assert listing["unread"] >= 1
    assert client.get(f"/api/schedules/{session['id']}", headers=user.headers).json()["reminder_sent"]


def test_reminder_says_the_configured_lead_time(client, user):
    """Regressão: a varredura (a cada 30 s) arredondava 14min50s para "em 14 minutos"."""
    session = _create(client, user, _now() + timedelta(minutes=15))
    # A varredura passa 10 s depois do horário do lembrete.
    _force_due(session["id"], _now() - timedelta(seconds=10))
    with SessionLocal() as db:
        db.execute(update(Schedule).where(Schedule.id == session["id"])
                   .values(start_at=_now() + timedelta(minutes=14, seconds=50)))
        db.commit()

    scan_reminders()
    message = next(n for n in _notifications(client, user)["items"]
                   if n["schedule_id"] == session["id"])["message"]
    assert message.startswith("Sua sessão de estudo começa em 15 minutos.")


def test_reminder_outside_grace_window_is_dropped(client, user):
    session = _create(client, user, _now() + timedelta(days=1))
    _force_due(session["id"], _now() - timedelta(minutes=200))
    scan_reminders()
    assert not [n for n in _notifications(client, user)["items"] if n["schedule_id"] == session["id"]]


def test_completed_session_is_not_reminded(client, user):
    session = _create(client, user, _now() + timedelta(minutes=15))
    client.patch(f"/api/schedules/{session['id']}/status", json={"status": "completed"},
                 headers=user.headers)
    _force_due(session["id"], _now())
    scan_reminders()
    assert not [n for n in _notifications(client, user)["items"] if n["schedule_id"] == session["id"]]


def test_message_formatting():
    class S:
        topic = "Fotossíntese"
        location = None

    assert format_reminder_message(S, 0).startswith("Sua sessão de estudo começa agora.")
    assert "em 1 minuto." in format_reminder_message(S, 1)
    assert "em 2 horas." in format_reminder_message(S, 120)
    assert "Tópico: Fotossíntese." in format_reminder_message(S, 5)


def test_mark_read_and_clear(client, user, make_user):
    session = _create(client, user, _now() + timedelta(minutes=15))
    _force_due(session["id"], _now())
    scan_reminders()
    item = next(n for n in _notifications(client, user)["items"] if n["schedule_id"] == session["id"])

    other = make_user()
    assert client.post(f"/api/notifications/{item['id']}/read", headers=other.headers).status_code == 404

    read = client.post(f"/api/notifications/{item['id']}/read", headers=user.headers).json()
    assert read["is_read"] is True
    client.post("/api/notifications/read-all", headers=user.headers)
    assert _notifications(client, user)["unread"] == 0
    client.delete("/api/notifications", headers=user.headers)
    assert _notifications(client, user)["items"] == []


def test_deleting_session_keeps_notification_without_link(client, user):
    session = _create(client, user, _now() + timedelta(minutes=15))
    _force_due(session["id"], _now())
    scan_reminders()
    client.delete(f"/api/schedules/{session['id']}", headers=user.headers)
    items = _notifications(client, user)["items"]
    assert any(n["title"] == "Lembrete: Revisão" and n["schedule_id"] is None for n in items)


def test_reminder_is_pushed_over_websocket(client, user):
    with client.websocket_connect(f"/api/ws/notifications?token={user.access}") as ws:
        assert ws.receive_json()["event"] == "connected"
        ws.send_json({"event": "ping"})
        assert ws.receive_json()["event"] == "pong"

        session = _create(client, user, _now() + timedelta(minutes=15))
        _force_due(session["id"], _now())
        scan_reminders()

        message = ws.receive_json()
        assert message["event"] == "notification"
        assert message["data"]["schedule_id"] == session["id"]
        assert message["data"]["schedule"]["minutes_left"] in (14, 15)


def test_websocket_rejects_bad_tokens(client, user):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    for token in ("", "abc", user.refresh):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/api/ws/notifications?token={token}") as ws:
                ws.receive_json()
