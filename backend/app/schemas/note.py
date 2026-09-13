"""Schemas de anotação."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.sanitize import normalize_tag, sanitize_html, sanitize_text
from app.schemas.common import ORMModel
from app.schemas.search import SearchResultRead
from app.schemas.subject import SubjectRead
from app.schemas.tag import TagRead

MAX_TAGS_PER_NOTE = 15


def _clean_tag_list(value: list[str] | None) -> list[str]:
    """Normaliza, remove duplicatas e limita a quantidade de tags."""
    if not value:
        return []
    seen: list[str] = []
    for raw in value:
        tag = normalize_tag(raw)
        if tag and len(tag) <= 60 and tag not in seen:
            seen.append(tag)
    return seen[:MAX_TAGS_PER_NOTE]


class NoteBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, examples=["Sistema circulatório"]
    )
    content: str = Field(default="", max_length=100_000)
    subject_id: int | None = None
    category: str | None = Field(default=None, max_length=60, examples=["Resumo"])
    is_pinned: bool = False
    tags: list[str] = Field(default_factory=list, examples=[["anatomia", "prova"]])

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O título não pode ficar vazio.")
        return cleaned

    @field_validator("content")
    @classmethod
    def _clean_content(cls, value: str) -> str:
        # Markdown é preservado; apenas HTML perigoso é removido.
        return sanitize_html(value) or ""

    @field_validator("category")
    @classmethod
    def _clean_category(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, value: list[str]) -> list[str]:
        return _clean_tag_list(value)


class NoteCreate(NoteBase):
    """Criação de anotação."""


class NoteUpdate(BaseModel):
    """Atualização parcial de anotação."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=100_000)
    subject_id: int | None = None
    category: str | None = Field(default=None, max_length=60)
    is_pinned: bool | None = None
    tags: list[str] | None = None

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("O título não pode ser nulo.")
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O título não pode ficar vazio.")
        return cleaned

    @field_validator("content")
    @classmethod
    def _clean_content(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("O conteúdo não pode ser nulo.")
        return sanitize_html(value) or ""

    @field_validator("is_pinned")
    @classmethod
    def _clean_pinned(cls, value: bool | None) -> bool | None:
        if value is None:
            raise ValueError("O campo fixado não pode ser nulo.")
        return value

    @field_validator("category")
    @classmethod
    def _clean_category(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_tag_list(value)


class NoteRead(ORMModel):
    """Anotação completa retornada pela API."""

    id: int
    title: str
    content: str
    category: str | None
    is_pinned: bool
    subject_id: int | None
    subject: SubjectRead | None = None
    tags: list[TagRead] = Field(default_factory=list)
    search_results: list[SearchResultRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class NoteSummary(ORMModel):
    """Versão enxuta usada em listagens e no dashboard."""

    id: int
    title: str
    category: str | None
    is_pinned: bool
    subject_id: int | None
    subject: SubjectRead | None = None
    tags: list[TagRead] = Field(default_factory=list)
    updated_at: datetime
    excerpt: str = ""
    links_count: int = 0
