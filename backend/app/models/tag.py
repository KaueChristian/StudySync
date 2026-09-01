"""Modelo de tag (etiqueta livre para organizar anotações)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampTZ

if TYPE_CHECKING:
    from app.models.note import Note


class Tag(Base):
    """
    Etiqueta pertencente a um usuário.

    O relacionamento com anotações é N:N (tabela `note_tags`), definido em
    `app.models.note` para evitar importação circular.
    """

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Sempre armazenada normalizada (minúscula, sem HTML) por `normalize_tag`.
    name: Mapped[str] = mapped_column(String(60), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ, server_default=func.now(), nullable=False
    )

    notes: Mapped[list["Note"]] = relationship(
        secondary="note_tags", back_populates="tags"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tag id={self.id} name={self.name!r}>"
