"""
Dependências compartilhadas das rotas.

Centraliza a resolução do usuário autenticado a partir do JWT, evitando que
cada rota repita a lógica de validação de token.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal, get_db
from app.models.user import User

# auto_error=False para devolvermos nossa própria mensagem em português.
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWT")

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou expiradas.",
    headers={"WWW-Authenticate": "Bearer"},
)

DbSession = Annotated[Session, Depends(get_db)]


def _load_active_user(db: Session, token: str) -> User:
    """Decodifica o access token e devolve o usuário ativo correspondente."""
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise CREDENTIALS_EXCEPTION from exc

    user = db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta está desativada.",
        )
    return user


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: DbSession,
) -> User:
    """Usuário autenticado via cabeçalho `Authorization: Bearer <token>`."""
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_EXCEPTION
    return _load_active_user(db, credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def authenticate_websocket(token: Annotated[str | None, Query()] = None) -> int:
    """
    Autentica uma conexão WebSocket.

    A API de WebSocket do navegador não permite cabeçalhos customizados, então
    o token trafega na query string. Como a conexão é `wss://` em produção, a
    query string é criptografada em trânsito — ainda assim, o access token de
    vida curta (30 min) limita a janela de exposição em logs de proxy.

    Returns:
        O id do usuário autenticado.
    """
    if not token:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise CREDENTIALS_EXCEPTION from exc

    # Sessão própria: a dependência `get_db` do FastAPI não roda em WebSockets
    # com o mesmo ciclo de vida das rotas HTTP.
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise CREDENTIALS_EXCEPTION
    return user_id


def get_user_by_ics_token(token: Annotated[str, Query()], db: DbSession) -> User:
    """
    Autentica a assinatura pública da agenda em `.ics`.

    Apps de calendário (Google/Apple) buscam a URL periodicamente sem enviar
    cabeçalhos customizados, então o token opaco trafega na própria query —
    mesmo raciocínio do token do WebSocket em `authenticate_websocket`.
    """
    user = db.scalar(select(User).where(User.ics_token == token))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link de agenda inválido."
        )
    return user


UserFromIcsToken = Annotated[User, Depends(get_user_by_ics_token)]
