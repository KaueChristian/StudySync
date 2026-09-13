"""Schemas de agendamento de sessão de estudo."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.sanitize import sanitize_text
from app.models.schedule import ScheduleStatus
from app.schemas.common import ORMModel
from app.schemas.search import SearchResultRead
from app.schemas.subject import SubjectRead

MAX_DURATION_HOURS = 24
MAX_RECURRENCE_WEEKS = 52


def _to_utc(value: datetime) -> datetime:
    """
    Converte para UTC.

    Datas ingênuas (sem fuso) são interpretadas como UTC — o frontend sempre
    envia ISO-8601 com offset, então isso é apenas uma salvaguarda.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ScheduleBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, examples=["Revisão de anatomia"]
    )
    topic: str | None = Field(
        default=None, max_length=255, examples=["Partes do corpo humano"]
    )
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=160, examples=["Biblioteca"])
    subject_id: int | None = None

    start_at: datetime = Field(..., examples=["2026-09-01T14:00:00-03:00"])
    end_at: datetime = Field(..., examples=["2026-09-01T15:30:00-03:00"])

    remind_minutes: int = Field(default=15, ge=0, le=1440)
    reminder_enabled: bool = True

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O título não pode ficar vazio.")
        return cleaned

    @field_validator("topic", "description", "location")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("start_at", "end_at")
    @classmethod
    def _normalize_datetime(cls, value: datetime) -> datetime:
        return _to_utc(value)

    @model_validator(mode="after")
    def _check_interval(self) -> "ScheduleBase":
        if self.end_at <= self.start_at:
            raise ValueError("O horário de término deve ser posterior ao de início.")
        duration = (self.end_at - self.start_at).total_seconds() / 3600
        if duration > MAX_DURATION_HOURS:
            raise ValueError(
                f"A sessão não pode ultrapassar {MAX_DURATION_HOURS} horas."
            )
        return self


class ScheduleCreate(ScheduleBase):
    """Criação de agendamento."""

    repeat_weekly: bool = False
    repeat_until: datetime | None = Field(
        default=None,
        description="Última data em que uma ocorrência semanal pode começar.",
    )

    @field_validator("repeat_until")
    @classmethod
    def _normalize_repeat_until(cls, value: datetime | None) -> datetime | None:
        return _to_utc(value) if value else None

    @model_validator(mode="after")
    def _check_recurrence(self) -> "ScheduleCreate":
        if not self.repeat_weekly:
            return self
        if self.repeat_until is None:
            raise ValueError(
                "Informe até quando a sessão deve se repetir."
            )
        if self.repeat_until <= self.start_at:
            raise ValueError(
                "A repetição deve terminar depois do início da primeira sessão."
            )
        max_span = timedelta(weeks=MAX_RECURRENCE_WEEKS)
        if self.repeat_until - self.start_at > max_span:
            raise ValueError(
                f"A repetição não pode ultrapassar {MAX_RECURRENCE_WEEKS} semanas."
            )
        return self


class ScheduleUpdate(BaseModel):
    """Atualização parcial de agendamento."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    topic: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=160)
    subject_id: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    remind_minutes: int | None = Field(default=None, ge=0, le=1440)
    reminder_enabled: bool | None = None
    status: ScheduleStatus | None = None

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("O título não pode ser nulo.")
        cleaned = sanitize_text(value)
        if not cleaned:
            raise ValueError("O título não pode ficar vazio.")
        return cleaned

    @field_validator("topic", "description", "location")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        return sanitize_text(value) or None

    @field_validator("start_at")
    @classmethod
    def _clean_start_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            raise ValueError("O horário de início não pode ser nulo.")
        return _to_utc(value)

    @field_validator("end_at")
    @classmethod
    def _clean_end_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            raise ValueError("O horário de término não pode ser nulo.")
        return _to_utc(value)

    @field_validator("remind_minutes")
    @classmethod
    def _clean_remind_minutes(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("A antecedência do lembrete não pode ser nula.")
        return value

    @field_validator("reminder_enabled")
    @classmethod
    def _clean_reminder_enabled(cls, value: bool | None) -> bool | None:
        if value is None:
            raise ValueError("O lembrete ativo não pode ser nulo.")
        return value

    @field_validator("status")
    @classmethod
    def _clean_status(cls, value: ScheduleStatus | None) -> ScheduleStatus | None:
        if value is None:
            raise ValueError("O status não pode ser nulo.")
        return value

    @model_validator(mode="after")
    def _check_interval(self) -> "ScheduleUpdate":
        # A validação cruzada completa (contra os valores já persistidos)
        # acontece na rota; aqui rejeitamos casos inválidos no payload.
        if self.start_at and self.end_at:
            if self.end_at <= self.start_at:
                raise ValueError("O horário de término deve ser posterior ao de início.")
            duration = (self.end_at - self.start_at).total_seconds() / 3600
            if duration > MAX_DURATION_HOURS:
                raise ValueError(
                    f"A sessão não pode ultrapassar {MAX_DURATION_HOURS} horas."
                )
        return self


class ScheduleStatusUpdate(BaseModel):
    """Alteração isolada do status (concluir / cancelar / reabrir)."""

    status: ScheduleStatus


class ScheduleRead(ORMModel):
    """Agendamento retornado pela API."""

    id: int
    title: str
    topic: str | None
    description: str | None
    location: str | None
    subject_id: int | None
    subject: SubjectRead | None = None

    start_at: datetime
    end_at: datetime

    remind_minutes: int
    remind_at: datetime | None
    reminder_enabled: bool
    reminder_sent: bool

    status: ScheduleStatus
    recurrence_group_id: str | None = None
    search_results: list[SearchResultRead] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime


class IcsTokenRead(BaseModel):
    """Token usado para montar a URL pública de assinatura da agenda."""

    token: str
