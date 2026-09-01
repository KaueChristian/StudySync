"""
Rotas de autenticação: cadastro, login, renovação e logout.

Estratégia de token
-------------------
* `access_token`  — 30 min, enviado em `Authorization: Bearer` a cada request.
* `refresh_token` — 7 dias, persistido (hash) e **rotacionado**: cada uso
  invalida o anterior e emite um novo par.

Detecção de reuso: se um refresh já revogado for apresentado, todas as sessões
do usuário são derrubadas — comportamento padrão contra roubo de token.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DbSession
from app.core.rate_limit import auth_limiter, client_ip, enforce_auth_rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenPair,
    TokenRefreshResponse,
)
from app.schemas.common import Message
from app.schemas.user import PasswordChange, UserCreate, UserRead, UserUpdate

logger = logging.getLogger("studysync.auth")

router = APIRouter()

RateLimited = Annotated[None, Depends(enforce_auth_rate_limit)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _issue_token_pair(db: DbSession, user: User, request: Request) -> TokenPair:
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
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            ip_address=client_ip(request)[:64],
        )
    )
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        user=UserRead.model_validate(user),
    )


def _revoke_all_sessions(db: DbSession, user_id: int) -> None:
    """Revoga todos os refresh tokens ativos de um usuário."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo usuário",
)
def register(
    payload: UserCreate, request: Request, db: DbSession, _: RateLimited = None
) -> TokenPair:
    """Cria a conta e já devolve os tokens (login automático)."""
    exists = db.scalar(select(User.id).where(User.email == payload.email))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        timezone=payload.timezone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Corrida entre duas requisições simultâneas com o mesmo e-mail.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        ) from None
    db.refresh(user)

    logger.info("Novo usuário cadastrado: id=%s", user.id)
    return _issue_token_pair(db, user, request)


@router.post("/login", response_model=TokenPair, summary="Autenticar usuário")
def login(
    payload: LoginRequest, request: Request, db: DbSession, _: RateLimited = None
) -> TokenPair:
    """Valida as credenciais e devolve o par de tokens."""
    user = db.scalar(select(User).where(User.email == payload.email))

    # Mensagem genérica e verificação sempre executada: evita distinguir
    # "e-mail inexistente" de "senha errada" (enumeração de contas) e reduz o
    # canal lateral de tempo.
    password_ok = verify_password(
        payload.password,
        user.hashed_password
        if user
        else "$2b$12$abcdefghijklmnopqrstuvCJz1YWfLxV1cUv1o1Ac.mJ1yQ3nWQ5S",
    )

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta está desativada.",
        )

    # Login bem-sucedido libera o contador de tentativas deste IP.
    auth_limiter.reset(f"{client_ip(request)}:{request.url.path}")

    return _issue_token_pair(db, user, request)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Renovar o token de acesso",
)
def refresh_tokens(
    payload: RefreshRequest, request: Request, db: DbSession
) -> TokenRefreshResponse:
    """Troca um refresh token válido por um novo par (com rotação)."""
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(claims["sub"])
        jti = claims["jti"]
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Faça login novamente.",
        ) from None

    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Faça login novamente.",
        )

    if stored.revoked:
        # Token já usado sendo apresentado de novo: possível vazamento.
        logger.warning("Reuso de refresh token detectado (user_id=%s)", user_id)
        _revoke_all_sessions(db, user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão comprometida. Todas as sessões foram encerradas.",
        )

    if stored.token_hash != hash_token(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Faça login novamente.",
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Faça login novamente.",
        )

    # Rotação: o token apresentado morre aqui.
    stored.revoked = True
    db.add(stored)

    pair = _issue_token_pair(db, user, request)
    return TokenRefreshResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_at=pair.expires_at,
    )


@router.post("/logout", response_model=Message, summary="Encerrar a sessão atual")
def logout(payload: RefreshRequest, db: DbSession) -> Message:
    """Revoga o refresh token informado."""
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
        jti = claims["jti"]
    except (InvalidTokenError, KeyError):
        # Token já inválido — do ponto de vista do cliente, logout concluído.
        return Message(detail="Sessão encerrada.")

    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if stored and not stored.revoked:
        stored.revoked = True
        db.add(stored)
        db.commit()

    return Message(detail="Sessão encerrada.")


@router.post(
    "/logout-all", response_model=Message, summary="Encerrar todas as sessões"
)
def logout_all(current_user: CurrentUser, db: DbSession) -> Message:
    """Revoga todos os refresh tokens do usuário (todos os dispositivos)."""
    _revoke_all_sessions(db, current_user.id)
    return Message(detail="Todas as sessões foram encerradas.")


@router.get("/me", response_model=UserRead, summary="Dados do usuário autenticado")
def read_current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, summary="Atualizar perfil")
def update_current_user(
    payload: UserUpdate, current_user: CurrentUser, db: DbSession
) -> UserRead:
    """Atualiza nome, fuso horário e antecedência padrão de lembrete."""
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.post("/change-password", response_model=Message, summary="Trocar a senha")
def change_password(
    payload: PasswordChange, current_user: CurrentUser, db: DbSession
) -> Message:
    """Troca a senha e derruba as demais sessões por segurança."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta.",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente da atual.",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()

    _revoke_all_sessions(db, current_user.id)
    return Message(
        detail="Senha alterada com sucesso. Faça login novamente nos outros dispositivos."
    )
