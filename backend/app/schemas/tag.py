"""Schemas de tag."""

from __future__ import annotations

from app.schemas.common import ORMModel


class TagRead(ORMModel):
    """Tag retornada pela API."""

    id: int
    name: str


class TagWithCount(TagRead):
    """Tag acompanhada da quantidade de anotações associadas."""

    notes_count: int = 0
