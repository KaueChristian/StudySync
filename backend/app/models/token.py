"""Refresh tokens persistidos — permitem revogação e rotação de sessões."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    """
    Registro de um refresh token emitido.

    Guardamos apenas o `jti` e o digest SHA-256 do token — nunca o token em si.
    Isso viabiliza:
      * logout real (revogação imediata);
      * rotação: cada uso emite um novo token e revoga o anterior;
      * detecção de reuso de token já revogado (indício de vazamento).
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(TimestampTZ, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )

    # Metadados úteis para uma futura tela de "sessões ativas".
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RefreshToken user_id={self.user_id} revoked={self.revoked}>"
