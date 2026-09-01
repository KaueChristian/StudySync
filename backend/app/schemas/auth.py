"""Schemas de autenticação."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Credenciais de acesso."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(BaseModel):
    """Solicitação de renovação do token de acesso."""

    refresh_token: str = Field(..., min_length=10)


class TokenRefreshResponse(BaseModel):
    """Novo par de tokens após rotação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime = Field(..., description="Expiração do access token (UTC).")


class TokenPair(TokenRefreshResponse):
    """Resposta de login/cadastro: tokens + dados do usuário."""

    user: UserRead
