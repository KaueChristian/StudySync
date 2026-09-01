"""CRUD de agendamentos de sessões de estudo."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession, UserFromIcsToken
from app.db.base import ensure_utc
from app.models.schedule import Schedule, ScheduleStatus
from app.models.subject import Subject
from app.schemas.common import Message
from app.schemas.schedule import (
    IcsTokenRead,
    ScheduleCreate,
    ScheduleRead,
    ScheduleStatusUpdate,
    ScheduleUpdate,
)
from app.services.ics import build_ics
from app.services.scheduler import compute_remind_at

router = APIRouter()

# Campos cuja alteração exige recalcular `remind_at` e reabrir o lembrete.
REMINDER_FIELDS = {"start_at", "remind_minutes", "reminder_enabled"}

MAX_RECURRENCE_INSTANCES = 52

ICS_HEADERS = {"Content-Disposition": 'attachment; filename="studysync-agenda.ics"'}


def get_owned_schedule(db: DbSession, owner_id: int, schedule_id: int) -> Schedule:
    """Carrega um agendamento garantindo a titularidade."""
    schedule = db.scalar(
        select(Schedule)
        .where(Schedule.id == schedule_id, Schedule.owner_id == owner_id)
        .options(selectinload(Schedule.subject), selectinload(Schedule.search_results))
    )
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado."
        )
    return schedule


def _validate_subject(db: DbSession, owner_id: int, subject_id: int | None) -> None:
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
@router.get("", response_model=list[ScheduleRead], summary="Listar agendamentos")
def list_schedules(
    current_user: CurrentUser,
    db: DbSession,
    start: Annotated[
        datetime | None, Query(description="Início do intervalo (ISO-8601).")
    ] = None,
    end: Annotated[
        datetime | None, Query(description="Fim do intervalo (ISO-8601).")
    ] = None,
    subject_id: Annotated[int | None, Query()] = None,
    schedule_status: Annotated[ScheduleStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[ScheduleRead]:
    """
    Agendamentos do usuário dentro de um intervalo.

    O calendário do frontend consulta mês a mês passando `start`/`end`.
    """
    query = select(Schedule).where(Schedule.owner_id == current_user.id)

    if start:
        query = query.where(Schedule.start_at >= ensure_utc(start))
    if end:
        query = query.where(Schedule.start_at <= ensure_utc(end))
    if subject_id is not None:
        query = query.where(Schedule.subject_id == subject_id)
    if schedule_status is not None:
        query = query.where(Schedule.status == schedule_status)

    schedules = db.scalars(
        query.options(
            selectinload(Schedule.subject), selectinload(Schedule.search_results)
        )
        .order_by(Schedule.start_at)
        .limit(limit)
    ).all()

    return [ScheduleRead.model_validate(s) for s in schedules]


@router.get(
    "/upcoming", response_model=list[ScheduleRead], summary="Próximas sessões"
)
def list_upcoming(
    current_user: CurrentUser,
    db: DbSession,
    hours: Annotated[int, Query(ge=1, le=720)] = 168,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[ScheduleRead]:
    """Sessões pendentes que começam nas próximas `hours` horas."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=hours)

    schedules = db.scalars(
        select(Schedule)
        .where(
            Schedule.owner_id == current_user.id,
            Schedule.status == ScheduleStatus.PENDING,
            Schedule.end_at >= now,
            Schedule.start_at <= horizon,
        )
        .options(
            selectinload(Schedule.subject), selectinload(Schedule.search_results)
        )
        .order_by(Schedule.start_at)
        .limit(limit)
    ).all()

    return [ScheduleRead.model_validate(s) for s in schedules]


def _build_schedule(
    owner_id: int, fields: dict, start_at: datetime, end_at: datetime, recurrence_group_id: str | None
) -> Schedule:
    schedule = Schedule(
        owner_id=owner_id,
        recurrence_group_id=recurrence_group_id,
        **fields,
        start_at=start_at,
        end_at=end_at,
    )
    schedule.remind_at = compute_remind_at(
        start_at, fields["remind_minutes"], fields["reminder_enabled"]
    )
    # Sessão criada já com o horário de lembrete no passado não deve gerar
    # um alerta retroativo (relevante para as instâncias mais distantes de
    # uma série recorrente longa cujo início já passou não se aplica aqui,
    # mas mantém o mesmo comportamento da criação avulsa).
    if schedule.remind_at and schedule.remind_at < datetime.now(timezone.utc):
        schedule.reminder_sent = True
    return schedule


@router.get("/export", summary="Baixar a agenda em .ics")
def export_schedules(current_user: CurrentUser, db: DbSession) -> Response:
    """Gera o `.ics` de todas as sessões do usuário para download direto."""
    schedules = db.scalars(
        select(Schedule)
        .where(Schedule.owner_id == current_user.id)
        .order_by(Schedule.start_at)
        .limit(1000)
    ).all()
    content = build_ics(schedules, calendar_name=f"StudySync — {current_user.name}")
    return Response(content=content, media_type="text/calendar", headers=ICS_HEADERS)


@router.post(
    "/export-token", response_model=IcsTokenRead, summary="Gerar link de assinatura da agenda"
)
def create_export_token(current_user: CurrentUser, db: DbSession) -> IcsTokenRead:
    """
    Gera (uma vez) o token usado na URL pública de assinatura da agenda.

    Chamadas seguintes devolvem o mesmo token — regenerar exigiria um botão
    de "revogar" dedicado, que não existe ainda.
    """
    if not current_user.ics_token:
        current_user.ics_token = secrets.token_urlsafe(32)
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return IcsTokenRead(token=current_user.ics_token)


@router.get(
    "/export.ics", summary="Assinar a agenda (URL pública para apps de calendário)"
)
def export_schedules_public(user: UserFromIcsToken, db: DbSession) -> Response:
    """Mesma exportação de `/export`, autenticada pelo token da URL."""
    schedules = db.scalars(
        select(Schedule)
        .where(Schedule.owner_id == user.id)
        .order_by(Schedule.start_at)
        .limit(1000)
    ).all()
    content = build_ics(schedules, calendar_name=f"StudySync — {user.name}")
    return Response(content=content, media_type="text/calendar", headers=ICS_HEADERS)


@router.post(
    "",
    response_model=ScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar agendamento",
)
def create_schedule(
    payload: ScheduleCreate, current_user: CurrentUser, db: DbSession
) -> ScheduleRead:
    """
    Cria a sessão e já materializa o instante do lembrete.

    Quando `repeat_weekly=True`, materializa uma sessão por semana (mesmo
    horário) até `repeat_until`, todas compartilhando um
    `recurrence_group_id` — em vez de calcular a recorrência em tempo de
    leitura, o que exigiria reescrever toda consulta de agenda/lembrete.
    """
    _validate_subject(db, current_user.id, payload.subject_id)

    data = payload.model_dump(exclude={"repeat_weekly", "repeat_until", "start_at", "end_at"})
    duration = payload.end_at - payload.start_at

    recurrence_group_id = str(uuid.uuid4()) if payload.repeat_weekly else None

    first = _build_schedule(
        current_user.id, data, payload.start_at, payload.end_at, recurrence_group_id
    )
    db.add(first)

    if payload.repeat_weekly:
        cursor_start = payload.start_at + timedelta(weeks=1)
        instances = 1
        while cursor_start <= payload.repeat_until and instances < MAX_RECURRENCE_INSTANCES:
            db.add(
                _build_schedule(
                    current_user.id,
                    data,
                    cursor_start,
                    cursor_start + duration,
                    recurrence_group_id,
                )
            )
            cursor_start += timedelta(weeks=1)
            instances += 1

    db.commit()
    db.refresh(first)
    return ScheduleRead.model_validate(first)


@router.get(
    "/{schedule_id}", response_model=ScheduleRead, summary="Detalhar agendamento"
)
def read_schedule(
    schedule_id: int, current_user: CurrentUser, db: DbSession
) -> ScheduleRead:
    return ScheduleRead.model_validate(
        get_owned_schedule(db, current_user.id, schedule_id)
    )


@router.patch(
    "/{schedule_id}", response_model=ScheduleRead, summary="Atualizar agendamento"
)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ScheduleRead:
    schedule = get_owned_schedule(db, current_user.id, schedule_id)
    data = payload.model_dump(exclude_unset=True)

    if "subject_id" in data:
        _validate_subject(db, current_user.id, data["subject_id"])

    for field, value in data.items():
        setattr(schedule, field, value)

    # Validação cruzada com os valores já persistidos: o payload pode trazer
    # só `start_at`, e o novo início precisa continuar antes do fim gravado.
    start_at = ensure_utc(schedule.start_at)
    end_at = ensure_utc(schedule.end_at)
    if start_at and end_at and end_at <= start_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O horário de término deve ser posterior ao de início.",
        )

    if REMINDER_FIELDS & data.keys():
        schedule.remind_at = compute_remind_at(
            schedule.start_at, schedule.remind_minutes, schedule.reminder_enabled
        )
        # Reagendar reabre o lembrete, desde que ele ainda esteja no futuro.
        schedule.reminder_sent = bool(
            schedule.remind_at and schedule.remind_at < datetime.now(timezone.utc)
        )

    schedule.updated_at = datetime.now(timezone.utc)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ScheduleRead.model_validate(schedule)


@router.patch(
    "/{schedule_id}/status",
    response_model=ScheduleRead,
    summary="Alterar status (concluir / cancelar / reabrir)",
)
def update_status(
    schedule_id: int,
    payload: ScheduleStatusUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ScheduleRead:
    schedule = get_owned_schedule(db, current_user.id, schedule_id)
    schedule.status = payload.status

    # Concluir ou cancelar silencia o lembrete ainda não disparado.
    if payload.status in (ScheduleStatus.COMPLETED, ScheduleStatus.CANCELED):
        schedule.reminder_sent = True

    schedule.updated_at = datetime.now(timezone.utc)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ScheduleRead.model_validate(schedule)


@router.delete(
    "/{schedule_id}", response_model=Message, summary="Excluir agendamento"
)
def delete_schedule(
    schedule_id: int,
    current_user: CurrentUser,
    db: DbSession,
    scope: Annotated[
        Literal["this", "following", "all"],
        Query(description="Alcance da exclusão dentro de uma série recorrente."),
    ] = "this",
) -> Message:
    schedule = get_owned_schedule(db, current_user.id, schedule_id)

    if scope == "this" or schedule.recurrence_group_id is None:
        db.delete(schedule)
        db.commit()
        return Message(detail="Agendamento excluído com sucesso.")

    query = select(Schedule).where(
        Schedule.owner_id == current_user.id,
        Schedule.recurrence_group_id == schedule.recurrence_group_id,
    )
    if scope == "following":
        query = query.where(Schedule.start_at >= schedule.start_at)

    group = db.scalars(query).all()
    count = len(group)
    for item in group:
        db.delete(item)
    db.commit()
    return Message(detail=f"{count} sessão(ões) excluída(s) com sucesso.")
