"""Modelo de notificação (lembretes gerados pelo agendador)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """
    Aviso destinado a um usuário.

    Persistir a notificação (em vez de apenas emitir pelo WebSocket) garante
    que o usuário offline no momento do disparo veja o lembrete ao voltar.
    """

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # "reminder" | "info" | "success" | "warning"
    type: Mapped[str] = mapped_column(String(30), default="info", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Referência opcional ao agendamento que originou o lembrete.
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification id={self.id} type={self.type!r} read={self.is_read}>"
