"""Modelo de link de apoio salvo a partir do motor de busca."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.note import Note
    from app.models.schedule import Schedule
    from app.models.user import User


class SearchResult(Base):
    """
    Link de conteúdo de apoio salvo pelo usuário.

    Pode ser anexado a uma anotação **ou** a um agendamento (nunca aos dois ao
    mesmo tempo, nem a nenhum) — regra garantida pelo CheckConstraint abaixo.
    """

    __tablename__ = "search_results"
    __table_args__ = (
        CheckConstraint(
            "(note_id IS NOT NULL AND schedule_id IS NULL) "
            "OR (note_id IS NULL AND schedule_id IS NOT NULL)",
            name="exactly_one_parent",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), index=True, nullable=True
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Domínio de origem (ex.: "pt.wikipedia.org") — exibido como badge.
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Consulta que originou o resultado, útil para rastreabilidade.
    query: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="search_results")
    note: Mapped["Note | None"] = relationship(back_populates="search_results")
    schedule: Mapped["Schedule | None"] = relationship(back_populates="search_results")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SearchResult id={self.id} url={self.url!r}>"
