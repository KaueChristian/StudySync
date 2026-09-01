"""
Gerador de arquivos iCalendar (RFC 5545) para exportar a agenda de estudos.

Construção manual (sem dependência nova): o formato é simples o bastante —
uma lista de linhas `CHAVE:valor`, com escape de texto e quebra em 75
octetos — que trazer uma biblioteca só para isso não se justifica.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.models.schedule import Schedule, ScheduleStatus

_PRODID = "-//StudySync//Agenda de Estudos//PT-BR"


def _escape(text: str) -> str:
    """Escapa os caracteres especiais do formato (RFC 5545 §3.3.11)."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Quebra uma linha em continuações de até 75 octetos, como exige o RFC."""
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line

    parts = []
    chunk = data[:75]
    parts.append(chunk.decode("utf-8", errors="ignore"))
    rest = data[len(parts[0].encode("utf-8")):]
    while rest:
        chunk = rest[:74]
        parts.append(" " + chunk.decode("utf-8", errors="ignore"))
        rest = rest[len(chunk):]
    return "\r\n".join(parts)


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_ics(schedules: Iterable[Schedule], calendar_name: str = "StudySync") -> str:
    """Monta o conteúdo completo do arquivo `.ics` para as sessões dadas."""
    now = _format_dt(datetime.now(timezone.utc))

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{_PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]

    for schedule in schedules:
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:studysync-schedule-{schedule.id}@studysync.local")
        lines.append(f"DTSTAMP:{now}")
        lines.append(f"DTSTART:{_format_dt(schedule.start_at)}")
        lines.append(f"DTEND:{_format_dt(schedule.end_at)}")
        lines.append(f"SUMMARY:{_escape(schedule.title)}")

        description_parts = [p for p in (schedule.topic, schedule.description) if p]
        if description_parts:
            lines.append(f"DESCRIPTION:{_escape(chr(10).join(description_parts))}")

        if schedule.location:
            lines.append(f"LOCATION:{_escape(schedule.location)}")

        status = (
            "CANCELLED" if schedule.status == ScheduleStatus.CANCELED else "CONFIRMED"
        )
        lines.append(f"STATUS:{status}")

        if schedule.reminder_enabled and schedule.status == ScheduleStatus.PENDING:
            lines.append("BEGIN:VALARM")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:{_escape(schedule.title)}")
            lines.append(f"TRIGGER:-PT{max(0, schedule.remind_minutes)}M")
            lines.append("END:VALARM")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
