"""Listagem de tags do usuário."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession
from app.models.note import note_tags
from app.models.tag import Tag
from app.schemas.common import Message
from app.schemas.tag import TagWithCount

router = APIRouter()


@router.get(
    "", response_model=list[TagWithCount], summary="Listar tags com contagem de uso"
)
def list_tags(current_user: CurrentUser, db: DbSession) -> list[TagWithCount]:
    """Tags do usuário ordenadas pelas mais usadas."""
    rows = db.execute(
        select(Tag.id, Tag.name, func.count(note_tags.c.note_id).label("notes_count"))
        .outerjoin(note_tags, note_tags.c.tag_id == Tag.id)
        .where(Tag.owner_id == current_user.id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(note_tags.c.note_id).desc(), Tag.name)
    ).all()

    return [
        TagWithCount(id=row.id, name=row.name, notes_count=row.notes_count)
        for row in rows
    ]


@router.delete("/{tag_id}", response_model=Message, summary="Excluir tag")
def delete_tag(tag_id: int, current_user: CurrentUser, db: DbSession) -> Message:
    """Remove a tag e suas associações (as anotações são preservadas)."""
    tag = db.scalar(
        select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id)
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag não encontrada."
        )

    db.delete(tag)
    db.commit()
    return Message(detail="Tag excluída com sucesso.")
