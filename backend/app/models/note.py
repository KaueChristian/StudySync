"""Modelo de anotação e tabela de associação com tags."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.search_result import SearchResult
    from app.models.subject import Subject
    from app.models.tag import Tag
    from app.models.user import User


# Associação N:N entre anotações e tags.
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column(
        "note_id",
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Note(Base):
    """
    Anotação em Markdown vinculada (opcionalmente) a uma matéria.

    O conteúdo é sanitizado na escrita (ver `app.core.sanitize`) e renderizado
    no frontend com `react-markdown`, que não interpreta HTML bruto.
    """

    __tablename__ = "notes"
    __table_args__ = (
        # Índice composto: a listagem padrão filtra por dono e ordena por data.
        Index("ix_notes_owner_updated", "owner_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Categoria livre (ex.: "Resumo", "Exercícios", "Revisão").
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ----------------------------------------------------------- relações
    owner: Mapped["User"] = relationship(back_populates="notes")
    subject: Mapped["Subject | None"] = relationship(back_populates="notes")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=note_tags, back_populates="notes", lazy="selectin"
    )
    search_results: Mapped[list["SearchResult"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Note id={self.id} title={self.title!r}>"
