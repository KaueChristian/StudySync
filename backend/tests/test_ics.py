"""Exportação `.ics` (RFC 5545)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.schedule import Schedule, ScheduleStatus
from app.services.ics import _escape, build_ics


def _schedule(**overrides) -> Schedule:
    start = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    fields = dict(
        id=1,
        title="Revisão",
        topic=None,
        description=None,
        location=None,
        start_at=start,
        end_at=start + timedelta(hours=1),
        reminder_enabled=True,
        remind_minutes=15,
        status=ScheduleStatus.PENDING,
    )
    fields.update(overrides)
    return Schedule(**fields)


def _unfold(ics: str) -> list[str]:
    return ics.replace("\r\n ", "").split("\r\n")


@pytest.mark.parametrize("unit", ["ção ", "é", "—", "€ ", "😀", "a"])
def test_folding_never_loses_characters(unit):
    """Regressão: um caractere multibyte cortado entre duas continuações sumia."""
    description = unit * 200
    ics = build_ics([_schedule(description=description)])

    for line in ics.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75

    lines = _unfold(ics)
    value = next(line for line in lines if line.startswith("DESCRIPTION:") and len(line) > 30)
    assert value == "DESCRIPTION:" + _escape(description)


def test_escape_rules():
    assert _escape("a;b,c\\d\r\ne\rf") == "a\\;b\\,c\\\\d\\ne\\nf"


def test_event_fields_and_alarm():
    ics = build_ics([_schedule(topic="Ondas", description="Ler cap. 3", location="Sala 2")])
    lines = _unfold(ics)
    assert "DTSTART:20261005T140000Z" in lines
    assert "DTEND:20261005T150000Z" in lines
    assert "DESCRIPTION:Ondas\\nLer cap. 3" in lines
    assert "LOCATION:Sala 2" in lines
    assert "TRIGGER:-PT15M" in lines
    assert ics.endswith("END:VCALENDAR\r\n")


def test_canceled_or_done_sessions_have_no_alarm():
    canceled = _unfold(build_ics([_schedule(status=ScheduleStatus.CANCELED)]))
    assert "STATUS:CANCELLED" in canceled
    assert "BEGIN:VALARM" not in canceled
    done = _unfold(build_ics([_schedule(status=ScheduleStatus.COMPLETED)]))
    assert "BEGIN:VALARM" not in done


def test_export_routes(client, user, make_user):
    start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0)
    client.post(
        "/api/schedules",
        json={"title": "Física", "start_at": start.isoformat(),
              "end_at": (start + timedelta(hours=1)).isoformat()},
        headers=user.headers,
    )
    download = client.get("/api/schedules/export", headers=user.headers)
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/calendar")
    assert "SUMMARY:Física" in download.text

    token = client.post("/api/schedules/export-token", headers=user.headers).json()["token"]
    again = client.post("/api/schedules/export-token", headers=user.headers).json()["token"]
    assert token == again

    public = client.get("/api/schedules/export.ics", params={"token": token})
    assert public.status_code == 200 and "SUMMARY:Física" in public.text

    # O token de um usuário nunca mostra a agenda de outro.
    other = make_user()
    other_token = client.post("/api/schedules/export-token", headers=other.headers).json()["token"]
    assert "Física" not in client.get("/api/schedules/export.ics", params={"token": other_token}).text

    assert client.get("/api/schedules/export.ics", params={"token": "invalido"}).status_code == 404
    assert client.get("/api/schedules/export").status_code == 401
