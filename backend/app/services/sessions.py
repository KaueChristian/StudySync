"""
Emissão de sessões (par de tokens) — usada pelas rotas de autenticação e pelo
app desktop.

No desktop não existe tela de login: o launcher chama `issue_local_session`
e entrega os tokens à janela pela ponte do pywebview. A API continua exigindo
JWT normalmente — só quem roda dentro da janela recebe o token.
"""

from __future__ import annotations

import secrets
from zoneinfo import available_timezones

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
)
from app.db.session import SessionLocal
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenPair
from app.schemas.user import UserRead

# Domínio reservado para exemplos (RFC 2606): nunca é de ninguém, e o
# EmailStr aceita (`.local`/`localhost` são recusados como uso especial).
LOCAL_USER_EMAIL = "local@example.com"
LOCAL_USER_NAME = "Estudante"
DEFAULT_TIMEZONE = "America/Sao_Paulo"


def issue_token_pair(
    db: Session, user: User, *, user_agent: str | None, ip_address: str | None
) -> TokenPair:
    """Emite access + refresh e registra o refresh para permitir revogação."""
    access_token, expires_at = create_access_token(
        user.id, extra_claims={"email": user.email}
    )
    refresh_token, jti, refresh_expires = create_refresh_token(user.id)

    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_expires,
            user_agent=(user_agent or "")[:255] or None,
            ip_address=(ip_address or "")[:64] or None,
        )
    )
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        user=UserRead.model_validate(user),
    )


def issue_local_session(timezone_name: str | None = None) -> dict:
    """
    Sessão do usuário único do app desktop, criado na primeira chamada.

    A senha é aleatória e descartada: ninguém entra por `/auth/login` com essa
    conta. `timezone_name` (o fuso do Windows, informado pela janela) só é
    usado na criação — depois, o usuário ajusta nas Configurações.
    """
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == LOCAL_USER_EMAIL))
        if user is None:
            timezone = (
                timezone_name if timezone_name in available_timezones() else DEFAULT_TIMEZONE
            )
            user = User(
                name=LOCAL_USER_NAME,
                email=LOCAL_USER_EMAIL,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                timezone=timezone,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        pair = issue_token_pair(db, user, user_agent="StudySync desktop", ip_address="127.0.0.1")
        return pair.model_dump(mode="json")
