"""Schemas de notificação."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    """Notificação retornada pela API e emitida pelo WebSocket."""

    id: int
    type: str
    title: str
    message: str | None
    schedule_id: int | None
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    """Listagem com contador de não lidas (alimenta o badge do sino)."""

    items: list[NotificationRead]
    unread: int
