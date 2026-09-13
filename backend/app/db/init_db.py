"""
Inicialização do banco de dados.

Uso:
    python -m app.db.init_db          # aplica as migrations pendentes
    python -m app.db.init_db --reset  # APAGA e recria tudo (destrutivo)

O esquema é sempre gerenciado pelo Alembic — inclusive no boot da aplicação.
Antes, o boot usava `Base.metadata.create_all`, que cria tabelas mas não
registra a revisão aplicada: o banco nascia "sem versão", o
`alembic upgrade head` seguinte falhava com `table users already exists`, e
nenhuma migration nova (como a `0003`) chegava a esses bancos.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Os plugins de autogenerate do Alembic anunciam o próprio carregamento em INFO
# já no import — ruído no log de boot da aplicação. Precisa vir antes do import.
logging.getLogger("alembic.runtime.plugins").setLevel(logging.WARNING)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402

# Importar o pacote de modelos popula `Base.metadata` com todas as tabelas.
from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("studysync.db")

BACKEND_DIR = Path(__file__).resolve().parents[2]
VERSION_TABLE = "alembic_version"


def _alembic_config() -> Config:
    """
    Configuração do Alembic montada em código.

    Sem `alembic.ini` de propósito: o `env.py` só chama `fileConfig` quando há
    arquivo, e isso reconfiguraria (e silenciaria) o logging da aplicação. A
    URL do banco vem de `app.core.config`, lida pelo próprio `env.py`.
    """
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return config


def _current_revision() -> str | None:
    inspector = inspect(engine)
    if VERSION_TABLE not in inspector.get_table_names():
        return None
    with engine.connect() as connection:
        return connection.execute(
            text(f"SELECT version_num FROM {VERSION_TABLE}")
        ).scalar()


def _baseline_for_unversioned() -> str:
    """
    Revisão equivalente a um banco criado pelo `create_all` antigo.

    Só existe para bancos criados antes de o boot passar a usar o Alembic —
    daqui em diante todo banco nasce versionado. A `0003` verifica sozinha se a
    FK já existe, então carimbar `0002` também serve para bancos que já
    nasceram com ela.
    """
    inspector = inspect(engine)
    schedule_columns = {c["name"] for c in inspector.get_columns("schedules")}
    user_columns = {c["name"] for c in inspector.get_columns("users")}
    if "recurrence_group_id" in schedule_columns and "ics_token" in user_columns:
        return "0002"
    return "0001"


def init_database() -> str:
    """
    Deixa o esquema na revisão mais recente, sem perder dados.

    * banco vazio          → aplica todas as migrations;
    * banco sem versão     → carimba a revisão equivalente e aplica o restante;
    * banco versionado     → aplica só as migrations pendentes.

    Returns:
        A revisão em que o banco ficou.
    """
    config = _alembic_config()
    existing_tables = set(inspect(engine).get_table_names()) - {VERSION_TABLE}

    if existing_tables and _current_revision() is None:
        baseline = _baseline_for_unversioned()
        logger.warning(
            "Banco sem revisão do Alembic (criado pelo create_all antigo); "
            "carimbando como %s antes de aplicar as migrations pendentes",
            baseline,
        )
        command.stamp(config, baseline)

    command.upgrade(config, "head")
    engine.dispose()  # descarta conexões abertas antes das alterações de esquema

    revision = _current_revision()
    logger.info("Esquema do banco na revisão %s", revision)
    return revision or ""


def reset_database() -> None:
    """Apaga todas as tabelas e as recria pelas migrations — **destrutivo**."""
    logger.warning("Apagando todas as tabelas…")
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {VERSION_TABLE}"))
    init_database()
    logger.info("Banco recriado do zero.")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)-7s | %(message)s"
    )

    parser = argparse.ArgumentParser(description="Inicializa o banco do StudySync.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga e recria todas as tabelas (perde todos os dados).",
    )
    args = parser.parse_args()

    if args.reset:
        confirm = input("Isso apagará TODOS os dados. Digite 'sim' para confirmar: ")
        if confirm.strip().lower() != "sim":
            print("Operação cancelada.")
            return 1
        reset_database()
    else:
        revision = init_database()
        print(f"✔ Esquema na revisão {revision}")

    print(f"✔ Banco pronto em: {engine.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
