"""Schemas de matéria/disciplina."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.sanitize import sanitize_text
from app.schemas.common import ORMModel

HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, examples=["Biologia"])
    description: str | None = Field(default=None, max_length=2000)
    color: str = Field(default="#6366f1", examples=["#22c55e"])
    icon: str = Field(default="book-open", max_length=40)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O nome da matéria não pode ficar vazio.")
        return cleaned

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str) -> str:
        value = value.strip()
        if not HEX_COLOR.match(value):
            raise ValueError("Cor inválida. Use o formato hexadecimal (#RRGGBB).")
        return value.lower()

    @field_validator("icon")
    @classmethod
    def _clean_icon(cls, value: str) -> str:
        # Somente slug do ícone (a-z, 0-9 e hífen) — evita injeção via nome.
        cleaned = re.sub(r"[^a-z0-9-]", "", (value or "").lower())
        return cleaned or "book-open"


class SubjectCreate(SubjectBase):
    """Criação de matéria."""


class SubjectUpdate(BaseModel):
    """Atualização parcial de matéria."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = None
    icon: str | None = Field(default=None, max_length=40)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O nome da matéria não pode ficar vazio.")
        return cleaned

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not HEX_COLOR.match(value):
            raise ValueError("Cor inválida. Use o formato hexadecimal (#RRGGBB).")
        return value.lower()

    @field_validator("icon")
    @classmethod
    def _clean_icon(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = re.sub(r"[^a-z0-9-]", "", value.lower())
        return cleaned or "book-open"


class SubjectRead(ORMModel):
    """Matéria retornada pela API, com contadores agregados."""

    id: int
    name: str
    description: str | None
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime

    # Preenchidos pela rota (não são colunas do modelo).
    notes_count: int = 0
    schedules_count: int = 0
