"""
Inicialização do banco de dados.

Uso:
    python -m app.db.init_db          # cria as tabelas
    python -m app.db.init_db --reset  # APAGA e recria tudo (destrutivo)

Em produção prefira o Alembic (`alembic upgrade head`): o `create_all` não
versiona alterações de esquema.
"""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import inspect

# Importar o pacote de modelos popula `Base.metadata` com todas as tabelas.
from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("studysync.db")


def init_database() -> list[str]:
    """
    Cria as tabelas que ainda não existem.

    Returns:
        Nomes das tabelas criadas nesta execução.
    """
    inspector = inspect(engine)
    before = set(inspector.get_table_names())

    Base.metadata.create_all(bind=engine)

    after = set(inspect(engine).get_table_names())
    created = sorted(after - before)

    if created:
        logger.info("Tabelas criadas: %s", ", ".join(created))
    return created


def reset_database() -> None:
    """Apaga todas as tabelas e as recria — **destrutivo**."""
    logger.warning("Apagando todas as tabelas…")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
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
        created = init_database()
        if created:
            print(f"✔ Tabelas criadas: {', '.join(created)}")
        else:
            print("✔ Banco já estava atualizado — nenhuma tabela criada.")

    print(f"✔ Banco pronto em: {engine.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
