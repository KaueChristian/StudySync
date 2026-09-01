"""Schemas genéricos reutilizados por vários recursos."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base para schemas de leitura montados a partir de objetos ORM."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    """Resposta simples de confirmação."""

    detail: str = Field(..., examples=["Operação realizada com sucesso."])


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope padrão das listagens paginadas."""

    items: list[T]
    total: int = Field(..., description="Total de registros que atendem ao filtro.")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    pages: int = Field(..., ge=0, description="Quantidade total de páginas.")
