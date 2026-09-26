"""Matérias, anotações, tags, links salvos, painel e isolamento entre usuários."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _session(client, user, start, **extra):
    return client.post("/api/schedules", json={
        "title": "Sessão", "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(), **extra}, headers=user.headers).json()


# ---------------------------------------------------------------- matérias
def test_subject_crud_and_counts(client, user):
    subject = client.post("/api/subjects", json={"name": "Biologia", "color": "#22C55E",
                                                  "icon": "Leaf<script>"}, headers=user.headers).json()
    assert subject["color"] == "#22c55e"
    assert subject["icon"] == "leafscript"
    client.post("/api/notes", json={"title": "Célula", "subject_id": subject["id"]}, headers=user.headers)
    _session(client, user, _now() + timedelta(days=1), subject_id=subject["id"])

    listed = client.get("/api/subjects", headers=user.headers).json()
    assert listed[0]["notes_count"] == 1 and listed[0]["schedules_count"] == 1

    assert client.post("/api/subjects", json={"name": "BIOLOGIA"}, headers=user.headers).status_code == 409
    assert client.post("/api/subjects", json={"name": "x", "color": "verde"},
                       headers=user.headers).status_code == 422


def test_deleting_subject_cascades_and_cleans_tags(client, user):
    subject = client.post("/api/subjects", json={"name": "História"}, headers=user.headers).json()
    client.post("/api/notes", json={"title": "Império", "subject_id": subject["id"],
                                    "tags": ["exclusiva"]}, headers=user.headers)
    _session(client, user, _now() + timedelta(days=1), subject_id=subject["id"])

    assert client.delete(f"/api/subjects/{subject['id']}", headers=user.headers).status_code == 200
    assert client.get("/api/notes", headers=user.headers).json()["total"] == 0
    assert client.get("/api/schedules", headers=user.headers).json() == []
    assert client.get("/api/tags", headers=user.headers).json() == []


# ---------------------------------------------------------------- anotações
def test_note_filters_order_and_pagination(client, user):
    client.post("/api/notes", json={"title": "História do Império", "category": "Resumo",
                                    "tags": ["prova"]}, headers=user.headers)
    client.post("/api/notes", json={"title": "Química orgânica", "content": "cadeias",
                                    "is_pinned": True}, headers=user.headers)
    for i in range(3):
        client.post("/api/notes", json={"title": f"Nota {i}"}, headers=user.headers)

    page = client.get("/api/notes", params={"page_size": 2}, headers=user.headers).json()
    assert page["total"] == 5 and page["pages"] == 3
    assert page["items"][0]["title"] == "Química orgânica"  # fixada primeiro

    def titles(**params):
        return [n["title"] for n in client.get("/api/notes", params=params, headers=user.headers).json()["items"]]

    assert titles(search="historia") == ["História do Império"]  # sem acento
    assert titles(search="QUIMICA") == ["Química orgânica"]
    assert titles(search="%") == []  # curinga é literal
    assert titles(tag="PROVA") == ["História do Império"]
    assert titles(category="Resumo") == ["História do Império"]
    assert titles(sort="title", order="asc", page_size=100)[:2] == ["Química orgânica", "História do Império"]
    assert client.get("/api/notes/categories", headers=user.headers).json() == ["Resumo"]


def test_note_update_tags_and_orphans(client, user):
    note = client.post("/api/notes", json={"title": "T", "tags": ["a", "b", "A", " b "]},
                       headers=user.headers).json()
    assert sorted(t["name"] for t in note["tags"]) == ["a", "b"]
    updated = client.patch(f"/api/notes/{note['id']}", json={"tags": ["c"]}, headers=user.headers).json()
    assert [t["name"] for t in updated["tags"]] == ["c"]
    assert [t["name"] for t in client.get("/api/tags", headers=user.headers).json()] == ["c"]

    for field in ("title", "content", "is_pinned"):
        assert client.patch(f"/api/notes/{note['id']}", json={field: None},
                            headers=user.headers).status_code == 422
    # Desvincular da matéria é permitido.
    assert client.patch(f"/api/notes/{note['id']}", json={"subject_id": None},
                        headers=user.headers).status_code == 200


def test_note_limits(client, user):
    many = client.post("/api/notes", json={"title": "T", "tags": [f"t{i}" for i in range(30)]},
                       headers=user.headers).json()
    assert len(many["tags"]) == 15
    assert client.post("/api/notes", json={"title": "   "}, headers=user.headers).status_code == 422
    assert client.post("/api/notes", json={"title": "<b></b>"}, headers=user.headers).status_code == 422


# ------------------------------------------------------------ links salvos
def test_save_link_rules(client, user):
    note = client.post("/api/notes", json={"title": "Links"}, headers=user.headers).json()
    session = _session(client, user, _now() + timedelta(days=1))
    link = {"title": "Fotossíntese", "url": "https://example.com/foto/"}

    assert client.post("/api/search/save", json=link, headers=user.headers).status_code == 400
    both = {**link, "note_id": note["id"], "schedule_id": session["id"]}
    assert client.post("/api/search/save", json=both, headers=user.headers).status_code == 400

    first = client.post("/api/search/save", json={**link, "note_id": note["id"]}, headers=user.headers)
    again = client.post("/api/search/save", json={**link, "url": "https://example.com/foto",
                                                  "note_id": note["id"]}, headers=user.headers)
    assert first.status_code == 201 and again.json()["id"] == first.json()["id"]

    on_session = client.post("/api/search/save", json={**link, "schedule_id": session["id"]},
                             headers=user.headers)
    assert on_session.status_code == 201
    assert len(client.get("/api/search/saved", headers=user.headers).json()) == 2
    assert len(client.get(f"/api/notes/{note['id']}/links", headers=user.headers).json()) == 1

    assert client.post("/api/search/save", json={**link, "url": "javascript:alert(1)",
                                                 "note_id": note["id"]}, headers=user.headers).status_code == 422


def test_save_link_with_markup_only_title_is_422_not_500(client, user):
    """Regressão: título que vira vazio após a sanitização estourava o NOT NULL (500)."""
    note = client.post("/api/notes", json={"title": "Links"}, headers=user.headers).json()
    response = client.post("/api/search/save", json={
        "title": "<b></b>", "url": "https://example.com", "note_id": note["id"]}, headers=user.headers)
    assert response.status_code == 422


def test_search_query_validation(client, user):
    assert client.post("/api/search", json={"query": "<b></b>"}, headers=user.headers).status_code == 422
    assert client.post("/api/search", json={"query": "a"}, headers=user.headers).status_code == 422


# ------------------------------------------------------------------ painel
def test_dashboard_counts_in_user_timezone(client, make_user):
    user = make_user(timezone="America/Sao_Paulo")
    now = _now()
    running = _session(client, user, now - timedelta(minutes=10))  # em andamento
    _session(client, user, now - timedelta(hours=3))  # vencida
    future = _session(client, user, now + timedelta(days=2))
    client.patch(f"/api/schedules/{future['id']}/status", json={"status": "completed"},
                 headers=user.headers)

    body = client.get("/api/dashboard", headers=user.headers).json()
    stats = body["stats"]
    assert stats["sessions_pending"] == 2
    assert stats["sessions_overdue"] == 1
    assert stats["sessions_completed"] == 1
    assert [s["id"] for s in body["upcoming"]] == [running["id"]]
    assert len(body["weekly_activity"]) == 7


# -------------------------------------------------------------- isolamento
def test_other_users_resources_are_404(client, user, make_user):
    other = make_user()
    subject = client.post("/api/subjects", json={"name": "Privada"}, headers=user.headers).json()
    note = client.post("/api/notes", json={"title": "Privada", "tags": ["segredo"]},
                       headers=user.headers).json()
    session = _session(client, user, _now() + timedelta(days=1))
    saved = client.post("/api/search/save", json={"title": "x", "url": "https://example.com",
                                                  "note_id": note["id"]}, headers=user.headers).json()
    tag_id = note["tags"][0]["id"]

    h = other.headers
    checks = [
        client.get(f"/api/subjects/{subject['id']}", headers=h),
        client.patch(f"/api/subjects/{subject['id']}", json={"name": "x"}, headers=h),
        client.delete(f"/api/subjects/{subject['id']}", headers=h),
        client.get(f"/api/notes/{note['id']}", headers=h),
        client.patch(f"/api/notes/{note['id']}", json={"title": "x"}, headers=h),
        client.delete(f"/api/notes/{note['id']}", headers=h),
        client.get(f"/api/notes/{note['id']}/links", headers=h),
        client.get(f"/api/schedules/{session['id']}", headers=h),
        client.patch(f"/api/schedules/{session['id']}", json={"title": "x"}, headers=h),
        client.patch(f"/api/schedules/{session['id']}/status", json={"status": "completed"}, headers=h),
        client.delete(f"/api/schedules/{session['id']}", headers=h),
        client.delete(f"/api/search/saved/{saved['id']}", headers=h),
        client.delete(f"/api/tags/{tag_id}", headers=h),
        client.post("/api/search/save", json={"title": "x", "url": "https://e.com",
                                              "note_id": note["id"]}, headers=h),
    ]
    assert [r.status_code for r in checks] == [404] * len(checks)
    # E nada alheio aparece nas listagens.
    assert client.get("/api/notes", headers=h).json()["total"] == 0
    assert client.get("/api/search/saved", params={"note_id": note["id"]}, headers=h).json() == []


@pytest.mark.parametrize("path", ["/api/subjects", "/api/notes", "/api/schedules",
                                  "/api/tags", "/api/dashboard", "/api/notifications",
                                  "/api/search/saved"])
def test_every_listing_requires_auth(client, path):
    assert client.get(path).status_code == 401


def test_security_headers(client):
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
