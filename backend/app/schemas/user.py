"""Schemas de usuário."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.sanitize import sanitize_text
from app.schemas.common import ORMModel

# Pelo menos uma letra e um número; comprimento validado à parte.
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def validate_password_strength(value: str) -> str:
    """Regras mínimas de robustez da senha."""
    if len(value) < 8:
        raise ValueError("A senha deve ter no mínimo 8 caracteres.")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("A senha é longa demais (máximo de 72 bytes).")
    if not _HAS_LETTER.search(value):
        raise ValueError("A senha deve conter ao menos uma letra.")
    if not _HAS_DIGIT.search(value):
        raise ValueError("A senha deve conter ao menos um número.")
    return value


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, examples=["Ana Souza"])
    email: EmailStr = Field(..., examples=["ana@exemplo.com"])

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = sanitize_text(value)
        if not cleaned or len(cleaned) < 2:
            raise ValueError("Nome inválido.")
        return cleaned

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserCreate(UserBase):
    """Payload de cadastro."""

    password: str = Field(..., min_length=8, max_length=128, examples=["Estudo2024"])
    timezone: str = Field(default="America/Sao_Paulo", max_length=64)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    """Atualização parcial do perfil."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    default_reminder_minutes: int | None = Field(default=None, ge=0, le=1440)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = sanitize_text(value)
        if not cleaned or len(cleaned) < 2:
            raise ValueError("Nome inválido.")
        return cleaned


class PasswordChange(BaseModel):
    """Troca de senha do usuário autenticado."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserRead(ORMModel):
    """Representação pública do usuário — nunca inclui o hash da senha."""

    id: int
    name: str
    email: EmailStr
    is_active: bool
    timezone: str
    default_reminder_minutes: int
    created_at: datetime
