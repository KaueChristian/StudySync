"""O que o usuário digita é o que volta da API, em todos os recursos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.search import SearchQuery


def _future(hours: int = 48) -> tuple[str, str]:
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=hours)
    return start.isoformat(), (start + timedelta(hours=1)).isoformat()


def test_subject_name_with_symbols_survives_create_and_edit(client, user):
    created = client.post("/api/subjects", json={"name": "P&D > Pesquisa"}, headers=user.headers)
    assert created.status_code == 201, created.text
    assert created.json()["name"] == "P&D > Pesquisa"

    subject_id = created.json()["id"]
    edited = client.patch(
        f"/api/subjects/{subject_id}",
        json={"name": "P&D", "description": "Métodos & técnicas: x < y"},
        headers=user.headers,
    )
    assert edited.json()["name"] == "P&D"
    assert edited.json()["description"] == "Métodos & técnicas: x < y"


def test_subject_uniqueness_still_matches_symbols(client, user):
    client.post("/api/subjects", json={"name": "C & C++"}, headers=user.headers)
    duplicate = client.post("/api/subjects", json={"name": "c & c++"}, headers=user.headers)
    assert duplicate.status_code == 409


def test_note_markdown_title_category_and_tags_round_trip(client, user):
    content = "> citação\n\nSe `a < b && c` então -> ok\n\n```js\nif (x < 3) {}\n```"
    created = client.post(
        "/api/notes",
        json={
            "title": "Álgebra: x < 5 & y > 2",
            "content": content,
            "category": "Q&A",
            "tags": ["P&D", "c++"],
        },
        headers=user.headers,
    )
    assert created.status_code == 201, created.text
    note = created.json()
    assert note["title"] == "Álgebra: x < 5 & y > 2"
    assert note["content"] == content
    assert note["category"] == "Q&A"
    assert sorted(t["name"] for t in note["tags"]) == ["c++", "p&d"]

    # A busca encontra pelo mesmo texto que o usuário digitou.
    found = client.get("/api/notes", params={"search": "x < 5 & y"}, headers=user.headers)
    assert [n["id"] for n in found.json()["items"]] == [note["id"]]
    by_tag = client.get("/api/notes", params={"tag": "p&d"}, headers=user.headers)
    assert [n["id"] for n in by_tag.json()["items"]] == [note["id"]]


def test_schedule_text_fields_round_trip(client, user):
    start, end = _future()
    created = client.post(
        "/api/schedules",
        json={
            "title": "Revisão: P&D",
            "topic": "Ondas < 1 nm",
            "location": "Sala 3 & 4",
            "start_at": start,
            "end_at": end,
        },
        headers=user.headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert (body["title"], body["topic"], body["location"]) == (
        "Revisão: P&D",
        "Ondas < 1 nm",
        "Sala 3 & 4",
    )


def test_saved_link_title_keeps_ampersand(client, user):
    note = client.post("/api/notes", json={"title": "Links"}, headers=user.headers).json()
    saved = client.post(
        "/api/search/save",
        json={
            "title": "Tom & Jerry — história",
            "url": "https://example.com/a?b=1&c=2",
            "snippet": "Uso de <, > e & em HTML",
            "note_id": note["id"],
        },
        headers=user.headers,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["title"] == "Tom & Jerry — história"
    assert saved.json()["snippet"] == "Uso de <, > e & em HTML"


def test_search_query_is_sent_as_typed():
    assert SearchQuery(query="C & C++ ponteiros").query == "C & C++ ponteiros"


def test_user_name_round_trip(client, user):
    response = client.patch("/api/auth/me", json={"name": "Ana & Bia"}, headers=user.headers)
    assert response.json()["name"] == "Ana & Bia"
