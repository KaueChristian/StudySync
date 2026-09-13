"""CRUD de anotações, com filtros por matéria, tag, categoria e busca textual."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.core.sanitize import escape_like, strip_accents
from app.models.note import Note
from app.models.search_result import SearchResult
from app.models.subject import Subject
from app.models.tag import Tag
from app.schemas.common import Message, PaginatedResponse
from app.schemas.note import NoteCreate, NoteRead, NoteSummary, NoteUpdate
from app.schemas.search import SearchResultRead
from app.services.tags import cleanup_orphan_tags, resolve_tags

router = APIRouter()

SortField = Literal["updated_at", "created_at", "title"]

# Marcações Markdown removidas ao gerar o resumo de listagem.
_MARKDOWN_NOISE = re.compile(r"(```.*?```|`[^`]*`|[*_>#\[\]()!|~-]|\r)", re.DOTALL)


def _excerpt(content: str, length: int = 180) -> str:
    """Gera um resumo em texto puro a partir do Markdown."""
    plain = _MARKDOWN_NOISE.sub(" ", content or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:length] + ("…" if len(plain) > length else "")


def get_owned_note(db: DbSession, owner_id: int, note_id: int) -> Note:
    """Carrega uma anotação garantindo a titularidade."""
    note = db.scalar(
        select(Note)
        .where(Note.id == note_id, Note.owner_id == owner_id)
        .options(selectinload(Note.tags), selectinload(Note.search_results))
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Anotação não encontrada."
        )
    return note


def _validate_subject(db: DbSession, owner_id: int, subject_id: int | None) -> None:
    """Impede vincular a anotação a uma matéria de outro usuário."""
    if subject_id is None:
        return
    exists = db.scalar(
        select(Subject.id).where(
            Subject.id == subject_id, Subject.owner_id == owner_id
        )
    )
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Matéria inválida."
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedResponse[NoteSummary],
    summary="Listar anotações (paginado)",
)
def list_notes(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 12,
    subject_id: Annotated[int | None, Query()] = None,
    tag: Annotated[str | None, Query(max_length=60)] = None,
    category: Annotated[str | None, Query(max_length=60)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    sort: Annotated[SortField, Query()] = "updated_at",
    order: Annotated[Literal["asc", "desc"], Query()] = "desc",
) -> PaginatedResponse[NoteSummary]:
    """
    Lista as anotações do usuário aplicando os filtros informados.

    Todos os filtros usam parâmetros vinculados do SQLAlchemy — não há
    concatenação de SQL, o que elimina a superfície de SQL Injection.
    """
    base = select(Note).where(Note.owner_id == current_user.id)

    if subject_id is not None:
        base = base.where(Note.subject_id == subject_id)
    if category:
        base = base.where(Note.category == category)
    if tag:
        base = base.join(Note.tags).where(
            Tag.name == tag.lower().strip(), Tag.owner_id == current_user.id
        )
    if search:
        clean_search = strip_accents(search.strip())
        pattern = f"%{escape_like(clean_search)}%"
        base = base.where(
            or_(
                func.unaccent(Note.title).like(pattern, escape="\\"),
                func.unaccent(Note.content).like(pattern, escape="\\"),
            )
        )

    total = db.scalar(
        select(func.count()).select_from(base.order_by(None).subquery())
    ) or 0

    sort_column = {
        "updated_at": Note.updated_at,
        "created_at": Note.created_at,
        "title": func.unaccent(Note.title),
    }[sort]
    direction = sort_column.asc() if order == "asc" else sort_column.desc()

    notes = list(
        db.scalars(
            base.options(
                selectinload(Note.tags),
                selectinload(Note.subject),
                selectinload(Note.search_results),
            )
            # Fixadas sempre no topo, depois a ordenação escolhida.
            .order_by(Note.is_pinned.desc(), direction)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).unique().all()
    )

    items = []
    for note in notes:
        summary = NoteSummary.model_validate(note)
        summary.excerpt = _excerpt(note.content)
        summary.links_count = len(note.search_results)
        items.append(summary)

    return PaginatedResponse[NoteSummary](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/categories", response_model=list[str], summary="Listar categorias em uso"
)
def list_categories(current_user: CurrentUser, db: DbSession) -> list[str]:
    """Categorias distintas já utilizadas — alimenta o autocomplete."""
    rows = db.scalars(
        select(Note.category)
        .where(Note.owner_id == current_user.id, Note.category.is_not(None))
        .distinct()
        .order_by(Note.category)
    ).all()
    return [row for row in rows if row]


@router.post(
    "",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar anotação",
)
def create_note(
    payload: NoteCreate, current_user: CurrentUser, db: DbSession
) -> NoteRead:
    _validate_subject(db, current_user.id, payload.subject_id)

    note = Note(
        owner_id=current_user.id,
        title=payload.title,
        content=payload.content,
        subject_id=payload.subject_id,
        category=payload.category,
        is_pinned=payload.is_pinned,
    )
    note.tags = resolve_tags(db, current_user.id, payload.tags)

    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/{note_id}", response_model=NoteRead, summary="Detalhar anotação")
def read_note(note_id: int, current_user: CurrentUser, db: DbSession) -> NoteRead:
    return NoteRead.model_validate(get_owned_note(db, current_user.id, note_id))


@router.patch("/{note_id}", response_model=NoteRead, summary="Atualizar anotação")
def update_note(
    note_id: int, payload: NoteUpdate, current_user: CurrentUser, db: DbSession
) -> NoteRead:
    note = get_owned_note(db, current_user.id, note_id)
    data = payload.model_dump(exclude_unset=True)

    if "subject_id" in data:
        _validate_subject(db, current_user.id, data["subject_id"])

    if "tags" in data and data["tags"] is not None:
        note.tags = resolve_tags(db, current_user.id, data.pop("tags"))
    else:
        data.pop("tags", None)

    for field, value in data.items():
        setattr(note, field, value)
    note.updated_at = datetime.now(timezone.utc)

    db.add(note)
    db.commit()

    cleanup_orphan_tags(db, current_user.id)
    db.commit()

    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", response_model=Message, summary="Excluir anotação")
def delete_note(note_id: int, current_user: CurrentUser, db: DbSession) -> Message:
    note = get_owned_note(db, current_user.id, note_id)
    db.delete(note)
    db.commit()

    cleanup_orphan_tags(db, current_user.id)
    db.commit()
    return Message(detail="Anotação excluída com sucesso.")


@router.get(
    "/{note_id}/links",
    response_model=list[SearchResultRead],
    summary="Listar links de apoio da anotação",
)
def list_note_links(
    note_id: int, current_user: CurrentUser, db: DbSession
) -> list[SearchResultRead]:
    """Links salvos na anotação, do mais recente para o mais antigo."""
    get_owned_note(db, current_user.id, note_id)  # valida titularidade

    results = db.scalars(
        select(SearchResult)
        .where(SearchResult.note_id == note_id)
        .order_by(SearchResult.created_at.desc())
    ).all()

    return [SearchResultRead.model_validate(result) for result in results]
