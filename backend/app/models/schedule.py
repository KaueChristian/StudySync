"""Modelo de agendamento de sessão de estudo."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.search_result import SearchResult
    from app.models.subject import Subject
    from app.models.user import User


class ScheduleStatus(str, enum.Enum):
    """Ciclo de vida de uma sessão de estudo."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Schedule(Base):
    """
    Sessão de estudo agendada.

    O campo derivado `remind_at` (= `start_at` - `remind_minutes`) é
    materializado em coluna indexada: o agendador varre a tabela a cada
    30 segundos e precisa dessa consulta barata, sem calcular em Python.
    """

    __tablename__ = "schedules"
    __table_args__ = (
        # Consulta quente do APScheduler: lembretes pendentes já vencidos.
        Index("ix_schedules_reminder_scan", "reminder_sent", "remind_at"),
        Index("ix_schedules_owner_start", "owner_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Assunto específico a ser estudado — também alimenta a busca de conteúdo.
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)

    # ------------------------------------------------------------ tempo
    start_at: Mapped[datetime] = mapped_column(TimestampTZ, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(TimestampTZ, nullable=False)

    # ---------------------------------------------------------- lembrete
    remind_minutes: Mapped[int] = mapped_column(default=15, nullable=False)
    remind_at: Mapped[datetime | None] = mapped_column(TimestampTZ, nullable=True)
    reminder_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[ScheduleStatus] = mapped_column(
        SAEnum(ScheduleStatus, native_enum=False, length=20),
        default=ScheduleStatus.PENDING,
        nullable=False,
    )

    # UUID compartilhado por todas as instâncias de uma série recorrente
    # (ver `services/scheduler.py` — cada instância é uma sessão materializada
    # normalmente, sem regra recorrente calculada em tempo de leitura).
    recurrence_group_id: Mapped[str | None] = mapped_column(
        String(36), index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ----------------------------------------------------------- relações
    owner: Mapped["User"] = relationship(back_populates="schedules")
    subject: Mapped["Subject | None"] = relationship(back_populates="schedules")
    search_results: Mapped[list["SearchResult"]] = relationship(
        back_populates="schedule",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Schedule id={self.id} title={self.title!r} start_at={self.start_at}>"
