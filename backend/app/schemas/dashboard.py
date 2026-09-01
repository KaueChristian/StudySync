"""Schemas do painel inicial."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.note import NoteSummary
from app.schemas.schedule import ScheduleRead


class DashboardStats(BaseModel):
    """Contadores exibidos nos cards do topo."""

    subjects: int
    notes: int
    saved_links: int
    sessions_upcoming: int
    sessions_completed: int
    sessions_today: int
    minutes_scheduled_week: int


class SubjectDistribution(BaseModel):
    """Distribuição de anotações por matéria (gráfico de barras)."""

    subject_id: int
    name: str
    color: str
    notes: int
    sessions: int


class DashboardResponse(BaseModel):
    """Payload completo do dashboard, servido em uma única requisição."""

    stats: DashboardStats
    upcoming: list[ScheduleRead]
    recent_notes: list[NoteSummary]
    distribution: list[SubjectDistribution]
    # Sessões concluídas por dia nos últimos 7 dias: [{"date": "...", "count": n}]
    weekly_activity: list[dict]
