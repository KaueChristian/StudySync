"""
Camada de segurança: hashing de senhas e emissão/validação de tokens JWT.

Decisões de projeto
-------------------
* **bcrypt** é usado diretamente (sem passlib) para evitar as camadas de
  compatibilidade legadas. O salt é gerado por senha e embutido no próprio hash.
* Dois tipos de token: `access` (curto, usado nas requisições) e `refresh`
  (longo, usado apenas para renovar o access). O `type` vai dentro do payload
  e é verificado, impedindo que um refresh seja usado como access.
* Cada token possui um `jti` (identificador único), o que permite revogação
  do refresh token no banco de dados.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings

TokenType = Literal["access", "refresh"]

# bcrypt trunca silenciosamente em 72 bytes; validamos antes para evitar que
# duas senhas diferentes com o mesmo prefixo sejam consideradas equivalentes.
MAX_PASSWORD_BYTES = 72


# ---------------------------------------------------------------------------
# Senhas
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Gera o hash bcrypt (com salt aleatório) de uma senha em texto puro."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"A senha excede o limite de {MAX_PASSWORD_BYTES} bytes suportado pelo bcrypt."
        )
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara, em tempo constante, uma senha em texto puro com seu hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:MAX_PASSWORD_BYTES],
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Hash malformado no banco — trata como falha de autenticação.
        return False


# ---------------------------------------------------------------------------
# Tokens JWT
# ---------------------------------------------------------------------------
def _create_token(
    subject: str | int,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    """
    Monta e assina um JWT.

    Returns:
        (token_codificado, jti, instante_de_expiracao)
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    jti = uuid.uuid4().hex

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expire


def create_access_token(
    subject: str | int, extra_claims: dict[str, Any] | None = None
) -> tuple[str, datetime]:
    """Cria o token de acesso de curta duração."""
    token, _, expire = _create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )
    return token, expire


def create_refresh_token(subject: str | int) -> tuple[str, str, datetime]:
    """
    Cria o token de renovação.

    Returns:
        (token, jti, expiracao) — o `jti` é persistido no banco para permitir
        revogação (logout) e rotação.
    """
    return _create_token(
        subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """
    Valida assinatura, expiração e tipo do token.

    Raises:
        InvalidTokenError: se o token for inválido, expirado ou de tipo incorreto.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "sub", "type", "jti"]},
    )
    if expected_type and payload.get("type") != expected_type:
        raise InvalidTokenError(
            f"Tipo de token inválido: esperado '{expected_type}', "
            f"recebido '{payload.get('type')}'."
        )
    return payload


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def hash_token(token: str) -> str:
    """
    Digest SHA-256 de um token.

    Refresh tokens nunca são gravados em texto puro: guardamos apenas o digest,
    de modo que um vazamento do banco não permita reutilizar sessões ativas.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secret(length: int = 64) -> str:
    """Gera uma chave aleatória segura (útil para popular SECRET_KEY)."""
    return secrets.token_urlsafe(length)
