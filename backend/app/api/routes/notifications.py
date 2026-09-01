"""Consulta e gerenciamento das notificações do usuário."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, func, select, update

from app.core.deps import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.common import Message
from app.schemas.notification import NotificationList, NotificationRead

router = APIRouter()


@router.get("", response_model=NotificationList, summary="Listar notificações")
def list_notifications(
    current_user: CurrentUser,
    db: DbSession,
    only_unread: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> NotificationList:
    """Notificações mais recentes e o total de não lidas (badge do sino)."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if only_unread:
        query = query.where(Notification.is_read.is_(False))

    items = db.scalars(
        query.order_by(Notification.created_at.desc()).limit(limit)
    ).all()

    unread = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ) or 0

    return NotificationList(
        items=[NotificationRead.model_validate(item) for item in items],
        unread=unread,
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Marcar notificação como lida",
)
def mark_as_read(
    notification_id: int, current_user: CurrentUser, db: DbSession
) -> NotificationRead:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada."
        )

    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return NotificationRead.model_validate(notification)


@router.post("/read-all", response_model=Message, summary="Marcar todas como lidas")
def mark_all_as_read(current_user: CurrentUser, db: DbSession) -> Message:
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    db.commit()
    return Message(detail=f"{result.rowcount} notificação(ões) marcada(s) como lida(s).")


@router.delete("", response_model=Message, summary="Limpar notificações lidas")
def clear_read(current_user: CurrentUser, db: DbSession) -> Message:
    result = db.execute(
        delete(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(True),
        )
    )
    db.commit()
    return Message(detail=f"{result.rowcount} notificação(ões) removida(s).")
