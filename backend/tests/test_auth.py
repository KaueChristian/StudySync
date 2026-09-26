"""Cadastro, login, tokens e perfil."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from tests.conftest import PASSWORD


def _login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_normalizes_email_and_rejects_duplicates(client):
    first = client.post("/api/auth/register", json={
        "name": "Caio", "email": "  Caio@Example.COM ", "password": PASSWORD})
    assert first.status_code == 201
    assert first.json()["user"]["email"] == "caio@example.com"
    again = client.post("/api/auth/register", json={
        "name": "Caio", "email": "caio@example.com", "password": PASSWORD})
    assert again.status_code == 409


@pytest.mark.parametrize("password", ["curta1", "semnumeros", "12345678", "á" * 40 + "1"])
def test_weak_or_oversized_passwords_rejected(client, password):
    response = client.post("/api/auth/register", json={
        "name": "Teste", "email": "fraca@example.com", "password": password})
    assert response.status_code == 422


def test_invalid_timezone_rejected(client):
    response = client.post("/api/auth/register", json={
        "name": "Teste", "email": "tz@example.com", "password": PASSWORD,
        "timezone": "Marte/Base_Alfa"})
    assert response.status_code == 422


def test_utc_in_any_case_is_stored_canonically(client):
    response = client.post("/api/auth/register", json={
        "name": "Teste", "email": "utc@example.com", "password": PASSWORD, "timezone": "utc"})
    assert response.status_code == 201
    assert response.json()["user"]["timezone"] == "UTC"


def test_login_errors_do_not_reveal_which_part_is_wrong(client, user):
    wrong_password = _login(client, user.email, "Errada123")
    unknown = _login(client, "ninguem@example.com")
    assert wrong_password.status_code == unknown.status_code == 401
    assert wrong_password.json()["detail"] == unknown.json()["detail"]
    assert _login(client, user.email.upper()).status_code == 200


def test_login_rate_limit(client, user):
    statuses = [_login(client, user.email, "Errada123").status_code for _ in range(11)]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_refresh_rotation_and_reuse_detection(client, user):
    first = client.post("/api/auth/refresh", json={"refresh_token": user.refresh})
    assert first.status_code == 200
    rotated = first.json()["refresh_token"]

    # O token antigo reapresentado derruba todas as sessões.
    reuse = client.post("/api/auth/refresh", json={"refresh_token": user.refresh})
    assert reuse.status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": rotated}).status_code == 401


def test_logout_revokes_refresh(client, user):
    assert client.post("/api/auth/logout", json={"refresh_token": user.refresh}).status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": user.refresh}).status_code == 401
    # Logout com lixo não é erro para o cliente.
    assert client.post("/api/auth/logout", json={"refresh_token": "x" * 20}).status_code == 200


def _forge(sub, token_type="access", **claims):
    now = datetime.now(timezone.utc)
    payload = {"sub": str(sub), "type": token_type, "jti": "x",
               "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=5)).timestamp())}
    payload.update(claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def test_tampered_or_wrong_tokens_are_401(client, user):
    header, body, signature = user.access.split(".")
    bad = [
        "",
        "Bearer",
        user.refresh,  # refresh usado como access
        f"{header}.{body}.{signature[::-1]}",
        jwt.encode({"sub": str(user.id), "type": "access", "jti": "x"}, "", algorithm="none")
        if hasattr(jwt, "encode") else "x",
        _forge(user.id, exp=int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp())),
        _forge(999_999),
        _forge("abc"),
    ]
    for token in bad:
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401, token
    assert client.get("/api/auth/me").status_code == 401


def test_profile_update_and_null_fields(client, user):
    response = client.patch("/api/auth/me", json={"default_reminder_minutes": 30,
                                                   "timezone": "Europe/Lisbon"},
                            headers=user.headers)
    assert response.status_code == 200
    assert response.json()["default_reminder_minutes"] == 30
    for field in ("name", "timezone", "default_reminder_minutes"):
        assert client.patch("/api/auth/me", json={field: None},
                            headers=user.headers).status_code == 422


def test_change_password_flow(client, user):
    wrong = client.post("/api/auth/change-password", json={
        "current_password": "Errada123", "new_password": "NovaSenha9"}, headers=user.headers)
    assert wrong.status_code == 400
    same = client.post("/api/auth/change-password", json={
        "current_password": PASSWORD, "new_password": PASSWORD}, headers=user.headers)
    assert same.status_code == 400
    ok = client.post("/api/auth/change-password", json={
        "current_password": PASSWORD, "new_password": "NovaSenha9"}, headers=user.headers)
    assert ok.status_code == 200
    assert _login(client, user.email, "NovaSenha9").status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": user.refresh}).status_code == 401
