"""
Agendador de tarefas em segundo plano (APScheduler).

Responsabilidades
-----------------
* **scan_reminders** (a cada `REMINDER_POLL_SECONDS`): encontra sessões cujo
  horário de lembrete já chegou, cria a notificação no banco e a empurra pelo
  WebSocket.
* **purge_expired_tokens** (diariamente): limpa refresh tokens expirados.

Por que polling e não um job por agendamento?
---------------------------------------------
Um job agendado por sessão exigiria reconstruir todos os jobs a cada reinício
e sincronizá-los em toda edição/exclusão. A varredura por índice
(`ix_schedules_reminder_scan`) custa microssegundos no SQLite e é resiliente a
reinícios: um lembrete perdido enquanto o servidor estava fora ainda dispara,
desde que esteja dentro da janela de tolerância (`REMINDER_GRACE_MINUTES`).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete, select

from app.core.config import settings
from app.db.base import ensure_utc
from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.schedule import Schedule, ScheduleStatus
from app.models.token import RefreshToken
from app.services.notifier import manager

logger = logging.getLogger("studysync.scheduler")

scheduler = BackgroundScheduler(
    timezone="UTC",
    job_defaults={
        "coalesce": True,       # execuções atrasadas viram uma só
        "max_instances": 1,     # nunca duas varreduras simultâneas
        "misfire_grace_time": 60,
    },
)


# ---------------------------------------------------------------------------
# Helpers de domínio
# ---------------------------------------------------------------------------
def compute_remind_at(
    start_at: datetime, remind_minutes: int, reminder_enabled: bool
) -> datetime | None:
    """Instante em que o lembrete deve disparar (ou `None` se desativado)."""
    if not reminder_enabled:
        return None
    start = ensure_utc(start_at)
    assert start is not None
    return start - timedelta(minutes=max(0, remind_minutes))


def format_reminder_message(schedule: Schedule, minutes_left: int) -> str:
    """Texto humanizado do lembrete."""
    if minutes_left <= 0:
        when = "agora"
    elif minutes_left == 1:
        when = "em 1 minuto"
    elif minutes_left < 60:
        when = f"em {minutes_left} minutos"
    else:
        hours = minutes_left // 60
        when = f"em {hours} hora{'s' if hours > 1 else ''}"

    parts = [f"Sua sessão de estudo começa {when}."]
    if schedule.topic:
        parts.append(f"Tópico: {schedule.topic}.")
    if schedule.location:
        parts.append(f"Local: {schedule.location}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
def scan_reminders() -> None:
    """Dispara os lembretes cujo horário já chegou."""
    now = datetime.now(timezone.utc)
    grace_floor = now - timedelta(minutes=settings.REMINDER_GRACE_MINUTES)

    try:
        with SessionLocal() as db:
            statement = (
                select(Schedule)
                .where(
                    Schedule.reminder_enabled.is_(True),
                    Schedule.reminder_sent.is_(False),
                    Schedule.status == ScheduleStatus.PENDING,
                    Schedule.remind_at.is_not(None),
                    Schedule.remind_at <= now,
                    # Ignora lembretes antigos demais (servidor esteve offline).
                    Schedule.remind_at >= grace_floor,
                )
                .order_by(Schedule.remind_at)
                .limit(100)
            )
            due = db.scalars(statement).all()

            if not due:
                return

            payloads: list[tuple[int, dict]] = []

            for schedule in due:
                start_at = ensure_utc(schedule.start_at)
                assert start_at is not None
                minutes_left = max(0, int((start_at - now).total_seconds() // 60))

                notification = Notification(
                    user_id=schedule.owner_id,
                    type="reminder",
                    title=f"Lembrete: {schedule.title}",
                    message=format_reminder_message(schedule, minutes_left),
                    schedule_id=schedule.id,
                )
                db.add(notification)
                schedule.reminder_sent = True
                db.flush()  # garante notification.id antes do commit

                payloads.append(
                    (
                        schedule.owner_id,
                        {
                            "event": "notification",
                            "data": {
                                "id": notification.id,
                                "type": notification.type,
                                "title": notification.title,
                                "message": notification.message,
                                "schedule_id": schedule.id,
                                "is_read": False,
                                "created_at": ensure_utc(
                                    notification.created_at or now
                                ).isoformat(),
                                "schedule": {
                                    "id": schedule.id,
                                    "title": schedule.title,
                                    "topic": schedule.topic,
                                    "start_at": start_at.isoformat(),
                                    "minutes_left": minutes_left,
                                },
                            },
                        },
                    )
                )

            db.commit()

        # Emissão fora da transação: o banco já está consistente, então uma
        # falha de rede aqui não deixa o lembrete "meio enviado".
        for user_id, payload in payloads:
            manager.send_to_user_threadsafe(user_id, payload)

        logger.info("Lembretes disparados: %d", len(payloads))

    except Exception:  # noqa: BLE001 — um job nunca deve derrubar o scheduler
        logger.exception("Falha ao processar lembretes")


def purge_expired_tokens() -> None:
    """Remove refresh tokens expirados ou revogados há mais de 7 dias."""
    now = datetime.now(timezone.utc)
    try:
        with SessionLocal() as db:
            result = db.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < now)
            )
            db.commit()
            if result.rowcount:
                logger.info("Refresh tokens expirados removidos: %d", result.rowcount)
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao limpar refresh tokens")


# ---------------------------------------------------------------------------
# Ciclo de vida
# ---------------------------------------------------------------------------
def start_scheduler() -> None:
    """Registra os jobs e inicia o agendador (chamado no startup da app)."""
    if scheduler.running:
        return

    scheduler.add_job(
        scan_reminders,
        trigger=IntervalTrigger(seconds=settings.REMINDER_POLL_SECONDS),
        id="scan_reminders",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=5),
    )
    scheduler.add_job(
        purge_expired_tokens,
        trigger=IntervalTrigger(hours=24),
        id="purge_expired_tokens",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Agendador iniciado (varredura de lembretes a cada %ds)",
        settings.REMINDER_POLL_SECONDS,
    )


def shutdown_scheduler() -> None:
    """Encerra o agendador de forma limpa (chamado no shutdown da app)."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Agendador encerrado")
