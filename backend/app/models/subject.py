"""Modelo de matéria/disciplina."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.note import Note
    from app.models.schedule import Schedule
    from app.models.user import User


class Subject(Base):
    """
    Uma disciplina (Biologia, Matemática, História…).

    É o agrupador de primeiro nível: anotações e agendamentos apontam para ela.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        # O nome da matéria é único por usuário, não globalmente.
        UniqueConstraint("owner_id", "name", name="uq_subject_owner_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cor em hexadecimal (#RRGGBB) usada nos badges e no calendário.
    color: Mapped[str] = mapped_column(String(7), default="#6366f1", nullable=False)
    # Nome do ícone (lucide-react) exibido no frontend.
    icon: Mapped[str] = mapped_column(String(40), default="book-open", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="subjects")
    notes: Mapped[list["Note"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Subject id={self.id} name={self.name!r}>"
