"""
Base declarativa do SQLAlchemy e utilitários de data/hora.

Todas as datas trafegam e são persistidas em **UTC**. A conversão para o fuso
do usuário acontece exclusivamente no frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

# Convenção de nomes para índices e constraints. Sem isso, o Alembic gera
# migrations que o SQLite não consegue aplicar (constraints anônimas).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UTCDateTime(TypeDecorator):
    """
    Coluna de data/hora que sempre entrega datetimes *aware* em UTC.

    Por que isso é necessário
    -------------------------
    O SQLite não tem tipo nativo de data: guarda uma string e **descarta o
    offset de fuso**. Sem esta camada, um `datetime` gravado como
    `2026-08-17 04:39+00:00` volta da consulta como ingênuo (`tzinfo=None`),
    e a partir daí:

      * o Pydantic serializa `"2026-08-17T04:39:00"` (sem o `Z`);
      * o navegador interpreta essa string como **horário local**;
      * o usuário vê o horário deslocado pelo seu fuso (3h no Brasil).

    Centralizar a conversão aqui garante que ORM, agendador, agregações do
    dashboard e respostas da API operem todos sobre o mesmo instante absoluto.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        """Python → banco: normaliza para UTC e remove o tzinfo."""
        if value is None:
            return None
        if value.tzinfo is None:
            # Convenção do projeto: datetime ingênuo já está em UTC.
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        """Banco → Python: reanexa o fuso UTC."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


# Tipo de coluna reutilizável para timestamps. Sempre UTC.
TimestampTZ = UTCDateTime()


def utcnow() -> datetime:
    """Instante atual como datetime *aware* em UTC."""
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    """
    Garante que um datetime seja *aware* em UTC.

    O SQLite não armazena o offset de fuso: valores lidos do banco voltam
    ingênuos (naive). Como só gravamos UTC, reanexamos o fuso na leitura.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
