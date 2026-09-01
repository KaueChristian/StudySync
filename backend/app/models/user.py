"""Modelo de usuário."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.note import Note
    from app.models.notification import Notification
    from app.models.schedule import Schedule
    from app.models.search_result import SearchResult
    from app.models.subject import Subject
    from app.models.token import RefreshToken


class User(Base):
    """Usuário autenticável — raiz de todos os dados da aplicação."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    # Hash bcrypt (salt incluso). Nunca exposto por nenhum schema de resposta.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Fuso horário IANA do usuário (ex.: "America/Sao_Paulo"), usado para
    # formatar as mensagens de lembrete.
    timezone: Mapped[str] = mapped_column(
        String(64), default="America/Sao_Paulo", nullable=False
    )
    # Antecedência padrão (minutos) sugerida ao criar um novo agendamento.
    default_reminder_minutes: Mapped[int] = mapped_column(default=15, nullable=False)

    # Token opaco usado para autenticar a assinatura pública da agenda em
    # `.ics` (apps de calendário externos não enviam cabeçalho Authorization).
    # Gerado sob demanda em `POST /schedules/export-token`.
    ics_token: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ----------------------------------------------------------- relações
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    search_results: Mapped[list["SearchResult"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # pragma: no cover - auxílio de depuração
        return f"<User id={self.id} email={self.email!r}>"
