"""Agendamentos: criação, recorrência, edição, status e exclusão."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest


def _payload(start: datetime, minutes: int = 60, **extra) -> dict:
    return {
        "title": "Sessão",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(minutes=minutes)).isoformat(),
        **extra,
    }


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _series(client, user, group_id):
    items = client.get("/api/schedules", params={"limit": 500}, headers=user.headers).json()
    return sorted(
        (s for s in items if s["recurrence_group_id"] == group_id),
        key=lambda s: s["start_at"],
    )


def test_create_computes_reminder(client, user):
    start = _now() + timedelta(days=1)
    body = client.post("/api/schedules", json=_payload(start, remind_minutes=30),
                       headers=user.headers).json()
    assert datetime.fromisoformat(body["remind_at"]) == start - timedelta(minutes=30)
    assert body["reminder_sent"] is False


def test_session_created_with_reminder_in_the_past_is_not_reminded(client, user):
    start = _now() + timedelta(minutes=5)
    body = client.post("/api/schedules", json=_payload(start, remind_minutes=30),
                       headers=user.headers).json()
    assert body["reminder_sent"] is True


@pytest.mark.parametrize(
    "start_delta, end_delta",
    [(0, 0), (60, 0), (0, 60 * 25)],
)
def test_invalid_intervals_rejected(client, user, start_delta, end_delta):
    base = _now() + timedelta(days=1)
    response = client.post(
        "/api/schedules",
        json={"title": "x", "start_at": (base + timedelta(minutes=start_delta)).isoformat(),
              "end_at": (base + timedelta(minutes=end_delta)).isoformat()},
        headers=user.headers,
    )
    assert response.status_code == 422


def test_patch_start_after_saved_end_rejected(client, user):
    start = _now() + timedelta(days=1)
    created = client.post("/api/schedules", json=_payload(start), headers=user.headers).json()
    response = client.patch(
        f"/api/schedules/{created['id']}",
        json={"start_at": (start + timedelta(hours=2)).isoformat()},
        headers=user.headers,
    )
    assert response.status_code == 422
    # A edição recusada não pode ter sido gravada.
    again = client.get(f"/api/schedules/{created['id']}", headers=user.headers).json()
    assert again["start_at"] == created["start_at"]


def test_patch_null_on_required_field_is_422(client, user):
    created = client.post("/api/schedules", json=_payload(_now() + timedelta(days=1)),
                          headers=user.headers).json()
    for field in ("title", "start_at", "end_at", "status", "remind_minutes"):
        response = client.patch(f"/api/schedules/{created['id']}", json={field: None},
                                headers=user.headers)
        assert response.status_code == 422, field


def test_weekly_recurrence_materializes_instances(client, user):
    start = _now() + timedelta(days=1)
    created = client.post(
        "/api/schedules",
        json=_payload(start, repeat_weekly=True,
                      repeat_until=(start + timedelta(weeks=4, hours=1)).isoformat()),
        headers=user.headers,
    ).json()
    series = _series(client, user, created["recurrence_group_id"])
    assert len(series) == 5
    starts = [datetime.fromisoformat(s["start_at"]) for s in series]
    assert all(b - a == timedelta(weeks=1) for a, b in zip(starts, starts[1:]))


def test_recurrence_capped_at_52(client, user):
    start = _now() + timedelta(days=1)
    created = client.post(
        "/api/schedules",
        json=_payload(start, repeat_weekly=True,
                      repeat_until=(start + timedelta(weeks=52)).isoformat()),
        headers=user.headers,
    ).json()
    assert len(_series(client, user, created["recurrence_group_id"])) == 52


def test_recurrence_keeps_local_time_across_dst(client, make_user):
    """Regressão: somar 7 dias em UTC mudava o horário local na troca de horário de verão."""
    user = make_user(timezone="America/New_York")
    tz = ZoneInfo("America/New_York")
    # 26/10/2026 14h (EDT); o horário de verão termina em 01/11/2026.
    first_local = datetime(2026, 10, 26, 14, 0, tzinfo=tz)
    created = client.post(
        "/api/schedules",
        json=_payload(first_local, repeat_weekly=True,
                      repeat_until=datetime(2026, 11, 20, tzinfo=tz).isoformat()),
        headers=user.headers,
    ).json()
    series = _series(client, user, created["recurrence_group_id"])
    assert len(series) == 4
    local_times = [datetime.fromisoformat(s["start_at"]).astimezone(tz) for s in series]
    assert [(t.hour, t.minute) for t in local_times] == [(14, 0)] * 4
    # A duração continua a mesma em todas as instâncias.
    for s in series:
        assert datetime.fromisoformat(s["end_at"]) - datetime.fromisoformat(s["start_at"]) == timedelta(hours=1)


@pytest.mark.parametrize("scope, remaining", [("this", 4), ("following", 2), ("all", 0)])
def test_delete_scopes(client, user, scope, remaining):
    start = _now() + timedelta(days=1)
    created = client.post(
        "/api/schedules",
        json=_payload(start, repeat_weekly=True,
                      repeat_until=(start + timedelta(weeks=4, hours=1)).isoformat()),
        headers=user.headers,
    ).json()
    group = created["recurrence_group_id"]
    third = _series(client, user, group)[2]
    response = client.delete(f"/api/schedules/{third['id']}", params={"scope": scope},
                             headers=user.headers)
    assert response.status_code == 200
    assert len(_series(client, user, group)) == remaining


def test_completing_silences_and_reopening_rearms_reminder(client, user):
    """Regressão: reabrir uma sessão futura deixava o lembrete silenciado para sempre."""
    start = _now() + timedelta(days=1)
    created = client.post("/api/schedules", json=_payload(start), headers=user.headers).json()
    sid = created["id"]

    done = client.patch(f"/api/schedules/{sid}/status", json={"status": "completed"},
                        headers=user.headers).json()
    assert done["reminder_sent"] is True

    reopened = client.patch(f"/api/schedules/{sid}/status", json={"status": "pending"},
                            headers=user.headers).json()
    assert reopened["status"] == "pending"
    assert reopened["reminder_sent"] is False


def test_reopening_a_past_session_does_not_remind_retroactively(client, user):
    start = _now() + timedelta(minutes=2)
    created = client.post("/api/schedules", json=_payload(start), headers=user.headers).json()
    client.patch(f"/api/schedules/{created['id']}/status", json={"status": "canceled"},
                 headers=user.headers)
    reopened = client.patch(f"/api/schedules/{created['id']}/status", json={"status": "pending"},
                            headers=user.headers).json()
    assert reopened["reminder_sent"] is True


def test_status_through_generic_patch_behaves_like_status_route(client, user):
    start = _now() + timedelta(days=1)
    created = client.post("/api/schedules", json=_payload(start), headers=user.headers).json()
    done = client.patch(f"/api/schedules/{created['id']}", json={"status": "completed"},
                        headers=user.headers).json()
    assert done["reminder_sent"] is True
    reopened = client.patch(f"/api/schedules/{created['id']}", json={"status": "pending"},
                            headers=user.headers).json()
    assert reopened["reminder_sent"] is False


def test_rescheduling_rearms_reminder(client, user):
    start = _now() + timedelta(minutes=3)
    created = client.post("/api/schedules", json=_payload(start), headers=user.headers).json()
    assert created["reminder_sent"] is True  # lembrete (15 min antes) já no passado
    new_start = start + timedelta(days=1)
    moved = client.patch(
        f"/api/schedules/{created['id']}",
        json={"start_at": new_start.isoformat(), "end_at": (new_start + timedelta(hours=1)).isoformat()},
        headers=user.headers,
    ).json()
    assert moved["reminder_sent"] is False


def test_list_filters_and_upcoming(client, user):
    subject = client.post("/api/subjects", json={"name": "Química"}, headers=user.headers).json()
    base = _now() + timedelta(days=3)
    client.post("/api/schedules", json=_payload(base, subject_id=subject["id"]), headers=user.headers)
    client.post("/api/schedules", json=_payload(base + timedelta(days=30)), headers=user.headers)

    window = client.get(
        "/api/schedules",
        params={"start": (base - timedelta(hours=1)).isoformat(), "end": (base + timedelta(hours=1)).isoformat()},
        headers=user.headers,
    ).json()
    assert len(window) == 1 and window[0]["subject"]["name"] == "Química"

    by_subject = client.get("/api/schedules", params={"subject_id": subject["id"]}, headers=user.headers).json()
    assert len(by_subject) == 1

    upcoming = client.get("/api/schedules/upcoming", params={"hours": 24 * 7}, headers=user.headers).json()
    assert [s["title"] for s in upcoming] == ["Sessão"]


def test_subject_of_another_user_is_rejected(client, user, make_user):
    other = make_user()
    foreign = client.post("/api/subjects", json={"name": "Alheia"}, headers=other.headers).json()
    response = client.post("/api/schedules",
                           json=_payload(_now() + timedelta(days=1), subject_id=foreign["id"]),
                           headers=user.headers)
    assert response.status_code == 400
