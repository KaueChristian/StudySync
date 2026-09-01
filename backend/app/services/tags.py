"""Utilitários de tags — resolução "get or create" por usuário."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.sanitize import normalize_tag
from app.models.tag import Tag


def resolve_tags(db: Session, owner_id: int, names: list[str]) -> list[Tag]:
    """
    Converte uma lista de nomes em objetos `Tag`, criando os que faltarem.

    As tags são normalizadas (minúsculas, sem HTML) e pertencem a um usuário,
    então dois usuários podem ter tags de mesmo nome sem colisão.
    """
    normalized = []
    for raw in names:
        name = normalize_tag(raw)
        if name and name not in normalized:
            normalized.append(name)

    if not normalized:
        return []

    existing = db.scalars(
        select(Tag).where(Tag.owner_id == owner_id, Tag.name.in_(normalized))
    ).all()
    by_name = {tag.name: tag for tag in existing}

    created: list[Tag] = []
    for name in normalized:
        if name not in by_name:
            tag = Tag(owner_id=owner_id, name=name)
            db.add(tag)
            created.append(tag)
            by_name[name] = tag

    if created:
        # Necessário para que as novas tags recebam PK antes da associação.
        db.flush()

    return [by_name[name] for name in normalized]


def cleanup_orphan_tags(db: Session, owner_id: int) -> int:
    """
    Remove tags do usuário que não estão associadas a nenhuma anotação.

    Chamado após edições/exclusões para que a nuvem de tags não acumule
    entradas mortas.
    """
    orphans = db.scalars(
        select(Tag).where(Tag.owner_id == owner_id, ~Tag.notes.any())
    ).all()
    for tag in orphans:
        db.delete(tag)
    return len(orphans)
