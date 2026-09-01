"""
Script de inicialização do servidor de desenvolvimento.

Uso:
    python run.py                       # http://localhost:8000
    python run.py --port 9000           # porta customizada
    python run.py --no-reload           # sem hot reload
    python run.py --host 0.0.0.0        # acessível na rede local
"""

from __future__ import annotations

import argparse

import uvicorn

from app.core.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor de desenvolvimento StudySync.")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta.")
    parser.add_argument("--port", type=int, default=8000, help="Porta de escuta.")
    parser.add_argument(
        "--no-reload", action="store_true", help="Desativa o recarregamento automático."
    )
    args = parser.parse_args()

    # Em produção o reload é sempre desligado (ele duplica o processo e, com
    # isso, duplicaria também o agendador de lembretes).
    reload_enabled = not args.no_reload and not settings.is_production

    print("=" * 64)
    print(f"  {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"  Ambiente : {settings.ENV}")
    print(f"  API      : http://{args.host}:{args.port}{settings.API_PREFIX}")
    if not settings.is_production:
        print(f"  Docs     : http://{args.host}:{args.port}/docs")
    print(f"  Banco    : {settings.sqlalchemy_url}")
    print(f"  CORS     : {', '.join(settings.cors_origins)}")
    print("=" * 64)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        log_level="info",
    )


if __name__ == "__main__":
    main()
