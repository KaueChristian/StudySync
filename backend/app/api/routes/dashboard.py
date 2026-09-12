"""Painel inicial — métricas agregadas em uma única requisição."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.db.base import ensure_utc
from app.models.note import Note
from app.models.schedule import Schedule, ScheduleStatus
from app.models.search_result import SearchResult
from app.models.subject import Subject
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardStats,
    SubjectDistribution,
)
from app.schemas.note import NoteSummary
from app.schemas.schedule import ScheduleRead

router = APIRouter()

_MARKDOWN_NOISE = re.compile(r"(```.*?```|`[^`]*`|[*_>#\[\]()!-]|\r)", re.DOTALL)


def _excerpt(content: str, length: int = 140) -> str:
    plain = _MARKDOWN_NOISE.sub(" ", content or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:length] + ("…" if len(plain) > length else "")


@router.get("", response_model=DashboardResponse, summary="Resumo do painel")
def get_dashboard(current_user: CurrentUser, db: DbSession) -> DashboardResponse:
    """
    Devolve tudo que o dashboard precisa em uma chamada.

    Agregar aqui evita a cascata de 5–6 requisições que o frontend faria para
    montar a mesma tela.
    """
    user_id = current_user.id
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=6)

    # ------------------------------------------------------------ contadores
    subjects_count = db.scalar(
        select(func.count(Subject.id)).where(Subject.owner_id == user_id)
    ) or 0
    notes_count = db.scalar(
        select(func.count(Note.id)).where(Note.owner_id == user_id)
    ) or 0
    links_count = db.scalar(
        select(func.count(SearchResult.id)).where(SearchResult.owner_id == user_id)
    ) or 0

    sessions_pending = db.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.PENDING,
        )
    ) or 0
    sessions_overdue = db.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.PENDING,
            Schedule.start_at < now,
        )
    ) or 0
    sessions_upcoming = db.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.PENDING,
            Schedule.start_at >= now,
        )
    ) or 0
    sessions_completed = db.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.COMPLETED,
        )
    ) or 0
    sessions_today = db.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.owner_id == user_id,
            Schedule.start_at >= today_start,
            Schedule.start_at < today_end,
        )
    ) or 0

    # Minutos planejados nos próximos 7 dias (soma das durações).
    week_sessions = db.scalars(
        select(Schedule).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.PENDING,
            Schedule.start_at >= today_start,
            Schedule.start_at < today_start + timedelta(days=7),
        )
    ).all()
    minutes_week = 0
    for session in week_sessions:
        start = ensure_utc(session.start_at)
        end = ensure_utc(session.end_at)
        if start and end:
            minutes_week += int((end - start).total_seconds() // 60)

    # ------------------------------------------------------- próximas sessões
    upcoming = db.scalars(
        select(Schedule)
        .where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.PENDING,
            Schedule.end_at >= now,
        )
        .options(
            selectinload(Schedule.subject), selectinload(Schedule.search_results)
        )
        .order_by(Schedule.start_at)
        .limit(5)
    ).all()

    # -------------------------------------------------------- notas recentes
    recent_notes = db.scalars(
        select(Note)
        .where(Note.owner_id == user_id)
        .options(
            selectinload(Note.subject),
            selectinload(Note.tags),
            selectinload(Note.search_results),
        )
        .order_by(Note.updated_at.desc())
        .limit(5)
    ).unique().all()

    note_summaries = []
    for note in recent_notes:
        summary = NoteSummary.model_validate(note)
        summary.excerpt = _excerpt(note.content)
        summary.links_count = len(note.search_results)
        note_summaries.append(summary)

    # --------------------------------------------------- distribuição/matéria
    note_by_subject = dict(
        db.execute(
            select(Note.subject_id, func.count(Note.id))
            .where(Note.owner_id == user_id, Note.subject_id.is_not(None))
            .group_by(Note.subject_id)
        ).all()
    )
    session_by_subject = dict(
        db.execute(
            select(Schedule.subject_id, func.count(Schedule.id))
            .where(Schedule.owner_id == user_id, Schedule.subject_id.is_not(None))
            .group_by(Schedule.subject_id)
        ).all()
    )
    subjects = db.scalars(
        select(Subject).where(Subject.owner_id == user_id).order_by(Subject.name)
    ).all()

    distribution = [
        SubjectDistribution(
            subject_id=subject.id,
            name=subject.name,
            color=subject.color,
            notes=note_by_subject.get(subject.id, 0),
            sessions=session_by_subject.get(subject.id, 0),
        )
        for subject in subjects
    ]

    # --------------------------------------------- atividade dos últimos 7 dias
    completed_week = db.scalars(
        select(Schedule).where(
            Schedule.owner_id == user_id,
            Schedule.status == ScheduleStatus.COMPLETED,
            Schedule.start_at >= week_start,
        )
    ).all()

    buckets: dict[str, int] = {
        (week_start + timedelta(days=offset)).date().isoformat(): 0
        for offset in range(7)
    }
    for session in completed_week:
        start = ensure_utc(session.start_at)
        if start:
            key = start.date().isoformat()
            if key in buckets:
                buckets[key] += 1

    weekly_activity = [
        {"date": day, "count": count} for day, count in sorted(buckets.items())
    ]

    return DashboardResponse(
        stats=DashboardStats(
            subjects=subjects_count,
            notes=notes_count,
            saved_links=links_count,
            sessions_pending=sessions_pending,
            sessions_overdue=sessions_overdue,
            sessions_upcoming=sessions_upcoming,
            sessions_completed=sessions_completed,
            sessions_today=sessions_today,
            minutes_scheduled_week=minutes_week,
        ),
        upcoming=[ScheduleRead.model_validate(s) for s in upcoming],
        recent_notes=note_summaries,
        distribution=distribution,
        weekly_activity=weekly_activity,
    )
