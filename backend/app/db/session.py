"""
Engine e fábrica de sessões do SQLAlchemy.

Notas sobre SQLite
------------------
* `check_same_thread=False` é necessário porque o FastAPI executa rotas
  síncronas em um pool de threads.
* `PRAGMA foreign_keys=ON` — o SQLite ignora chaves estrangeiras por padrão;
  sem isso os `ON DELETE CASCADE` não funcionam.
* `PRAGMA journal_mode=WAL` — permite leituras concorrentes com escritas,
  importante porque o agendador em background escreve enquanto a API lê.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.sqlalchemy_url.startswith("sqlite")

engine: Engine = create_engine(
    settings.sqlalchemy_url,
    connect_args={"check_same_thread": False, "timeout": 30} if _is_sqlite else {},
    pool_pre_ping=True,
    echo=False,
    future=True,
)


if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependência do FastAPI que fornece uma sessão por requisição.

    A sessão é fechada ao final; em caso de exceção é feito rollback para não
    deixar transações pendentes ocupando o pool.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
