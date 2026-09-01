"""Schemas do motor de busca / conteúdo de apoio."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.core.sanitize import sanitize_text
from app.schemas.common import ORMModel


class SearchQuery(BaseModel):
    """Parâmetros de uma busca de conteúdo de apoio."""

    query: str = Field(
        ...,
        min_length=2,
        max_length=300,
        examples=["Estudo sobre partes do corpo humano"],
    )
    limit: int = Field(default=5, ge=1, le=10)
    # Quando informado, o assunto da matéria é somado à consulta para
    # desambiguar termos genéricos (ex.: "célula" em Biologia vs. Química).
    subject_hint: str | None = Field(default=None, max_length=120)

    @field_validator("query", "subject_hint")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        cleaned = sanitize_text(value)
        return cleaned or None


class SearchResultItem(BaseModel):
    """Um resultado bruto retornado pelo scraper (ainda não salvo)."""

    title: str
    url: str
    snippet: str | None = None
    source: str | None = Field(default=None, description="Domínio de origem.")
    score: float = Field(default=0.0, description="Pontuação de relevância (0–100).")


class SearchResponse(BaseModel):
    """Resposta do endpoint de busca."""

    query: str = Field(..., description="Consulta efetivamente enviada ao buscador.")
    provider: str = Field(..., description="Buscador que respondeu.")
    cached: bool = False
    took_ms: int = 0
    results: list[SearchResultItem]


class SaveSearchResultRequest(BaseModel):
    """Payload para anexar um link a uma anotação ou agendamento."""

    title: str = Field(..., min_length=1, max_length=300)
    url: HttpUrl
    snippet: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=120)
    query: str | None = Field(default=None, max_length=300)

    note_id: int | None = None
    schedule_id: int | None = None

    @field_validator("title", "snippet", "source", "query")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None


class SearchResultRead(ORMModel):
    """Link de apoio persistido."""

    id: int
    title: str
    url: str
    snippet: str | None
    source: str | None
    query: str | None
    note_id: int | None
    schedule_id: int | None
    created_at: datetime
