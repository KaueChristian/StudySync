"""CRUD de matérias/disciplinas."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DbSession
from app.models.note import Note
from app.models.schedule import Schedule
from app.models.subject import Subject
from app.schemas.common import Message
from app.schemas.subject import SubjectCreate, SubjectRead, SubjectUpdate

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_owned_subject(db: DbSession, owner_id: int, subject_id: int) -> Subject:
    """
    Carrega uma matéria garantindo que pertence ao usuário.

    Devolver 404 (e não 403) quando o recurso é de outro usuário evita
    vazar a existência de IDs alheios.
    """
    subject = db.scalar(
        select(Subject).where(Subject.id == subject_id, Subject.owner_id == owner_id)
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Matéria não encontrada."
        )
    return subject


def _with_counts(db: DbSession, subjects: list[Subject]) -> list[SubjectRead]:
    """Anexa os contadores de anotações e agendamentos de cada matéria."""
    if not subjects:
        return []

    ids = [s.id for s in subjects]

    note_counts = dict(
        db.execute(
            select(Note.subject_id, func.count(Note.id))
            .where(Note.subject_id.in_(ids))
            .group_by(Note.subject_id)
        ).all()
    )
    schedule_counts = dict(
        db.execute(
            select(Schedule.subject_id, func.count(Schedule.id))
            .where(Schedule.subject_id.in_(ids))
            .group_by(Schedule.subject_id)
        ).all()
    )

    output: list[SubjectRead] = []
    for subject in subjects:
        item = SubjectRead.model_validate(subject)
        item.notes_count = note_counts.get(subject.id, 0)
        item.schedules_count = schedule_counts.get(subject.id, 0)
        output.append(item)
    return output


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("", response_model=list[SubjectRead], summary="Listar matérias")
def list_subjects(current_user: CurrentUser, db: DbSession) -> list[SubjectRead]:
    """Todas as matérias do usuário, em ordem alfabética."""
    subjects = list(
        db.scalars(
            select(Subject)
            .where(Subject.owner_id == current_user.id)
            .order_by(func.lower(Subject.name))
        ).all()
    )
    return _with_counts(db, subjects)


@router.post(
    "",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar matéria",
)
def create_subject(
    payload: SubjectCreate, current_user: CurrentUser, db: DbSession
) -> SubjectRead:
    subject = Subject(owner_id=current_user.id, **payload.model_dump())
    db.add(subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem uma matéria com esse nome.",
        ) from None
    db.refresh(subject)
    return SubjectRead.model_validate(subject)


@router.get("/{subject_id}", response_model=SubjectRead, summary="Detalhar matéria")
def read_subject(
    subject_id: int, current_user: CurrentUser, db: DbSession
) -> SubjectRead:
    subject = get_owned_subject(db, current_user.id, subject_id)
    return _with_counts(db, [subject])[0]


@router.patch("/{subject_id}", response_model=SubjectRead, summary="Atualizar matéria")
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> SubjectRead:
    subject = get_owned_subject(db, current_user.id, subject_id)

    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(subject, field, value)
    subject.updated_at = datetime.now(timezone.utc)

    db.add(subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem uma matéria com esse nome.",
        ) from None
    db.refresh(subject)
    return _with_counts(db, [subject])[0]


@router.delete("/{subject_id}", response_model=Message, summary="Excluir matéria")
def delete_subject(
    subject_id: int, current_user: CurrentUser, db: DbSession
) -> Message:
    """
    Exclui a matéria e, em cascata, suas anotações e agendamentos.

    A cascata é aplicada tanto no ORM quanto pelo `ON DELETE CASCADE` do SQLite
    (habilitado via `PRAGMA foreign_keys=ON`).
    """
    subject = get_owned_subject(db, current_user.id, subject_id)
    db.delete(subject)
    db.commit()
    return Message(detail="Matéria excluída com sucesso.")
