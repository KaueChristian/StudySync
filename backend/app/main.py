"""
Ponto de entrada da aplicação FastAPI.

Responsabilidades:
    * criar a aplicação e registrar os roteadores;
    * configurar CORS e cabeçalhos de segurança;
    * padronizar as respostas de erro;
    * iniciar/encerrar o agendador de tarefas em segundo plano.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_database
from app.services.notifier import manager
from app.services.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("studysync")


# ---------------------------------------------------------------------------
# Ciclo de vida
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startup e shutdown da aplicação."""
    logger.info("Iniciando %s v%s (%s)", settings.PROJECT_NAME, settings.VERSION, settings.ENV)

    # Aplica as migrations pendentes do Alembic (cria o banco do zero, se
    # preciso) — o mesmo caminho em desenvolvimento e em produção.
    init_database()

    # O agendador roda em outra thread e precisa de uma referência ao event
    # loop para conseguir emitir pelos WebSockets.
    manager.bind_loop(asyncio.get_running_loop())
    start_scheduler()

    yield

    shutdown_scheduler()
    logger.info("Aplicação encerrada")


# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Cabeçalhos de proteção aplicados a todas as respostas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API do StudySync — gerenciador de anotações, agendamentos de estudo "
        "e pesquisa de conteúdo de apoio."
    ),
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# CORS restrito às origens declaradas no .env — nunca "*", pois a API usa
# credenciais (Authorization) e uma origem curinga anularia a proteção.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Retry-After"],
    max_age=600,
)
app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Tratamento de erros
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Converte erros de validação do Pydantic em mensagens legíveis.

    O formato padrão do FastAPI é verboso demais para exibir direto na UI.
    """
    errors = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"] if part != "body")
        message = error.get("msg", "Valor inválido.")
        message = message.removeprefix("Value error, ")
        errors.append({"field": location or "payload", "message": message})

    first = errors[0]["message"] if errors else "Dados inválidos."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": first, "errors": errors}),
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Nunca expõe detalhes internos do banco ao cliente."""
    logger.exception("Erro de banco de dados: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno ao acessar os dados. Tente novamente."},
    )


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Sistema"], summary="Informações da API")
def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs" if not settings.is_production else None,
        "status": "online",
    }


@app.get("/health", tags=["Sistema"], summary="Verificação de saúde")
def health() -> dict:
    """Usado por monitoramento e pelo script de inicialização do frontend."""
    from app.services.scheduler import scheduler

    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "websocket_connections": manager.total_connections,
    }
