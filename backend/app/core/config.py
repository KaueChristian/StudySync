"""
Configuração central da aplicação.

Todos os parâmetros são lidos de variáveis de ambiente (ou do arquivo `.env`
na raiz de /backend) através do pydantic-settings, o que garante validação de
tipos logo no boot da aplicação.
"""

from __future__ import annotations

import secrets
import warnings
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do pacote backend/ (…/StudySync/backend)
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurações tipadas da aplicação."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ app
    PROJECT_NAME: str = "StudySync API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENV: str = "development"

    # ------------------------------------------------------------- segurança
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AUTH_RATE_LIMIT_MAX: int = 10
    AUTH_RATE_LIMIT_WINDOW: int = 60

    # --------------------------------------------------------------- banco
    DATABASE_URL: str = "sqlite:///./studysync.db"

    # ---------------------------------------------------------------- cors
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ----------------------------------------------------------- agendador
    REMINDER_POLL_SECONDS: int = 30
    REMINDER_GRACE_MINUTES: int = 120

    # ------------------------------------------------------------- scraper
    SCRAPER_TIMEOUT: float = 12.0
    SCRAPER_CACHE_TTL: int = 900
    SCRAPER_MAX_RESULTS: int = 5
    SCRAPER_REGION: str = "br-pt"

    # ------------------------------------------------------------ validação
    @field_validator("ENV")
    @classmethod
    def _normalize_env(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"development", "production", "test"}:
            raise ValueError("ENV deve ser 'development', 'production' ou 'test'")
        return value

    # ------------------------------------------------------- propriedades
    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Lista de origens permitidas pelo middleware de CORS."""
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def sqlalchemy_url(self) -> str:
        """
        Normaliza caminhos SQLite relativos para absolutos.

        Sem isso, o arquivo .db seria criado no diretório de onde o processo
        foi iniciado, e não dentro de /backend.
        """
        url = self.DATABASE_URL
        prefix = "sqlite:///"
        if url.startswith(prefix):
            raw_path = url[len(prefix) :]
            if raw_path.startswith("./") or not Path(raw_path).is_absolute():
                absolute = (BASE_DIR / raw_path.lstrip("./")).resolve()
                return f"{prefix}{absolute.as_posix()}"
        return url


@lru_cache
def get_settings() -> Settings:
    """Instância única (cacheada) das configurações."""
    settings = Settings()

    if not settings.SECRET_KEY:
        if settings.is_production:
            raise RuntimeError(
                "SECRET_KEY é obrigatória quando ENV=production. "
                'Gere uma com: python -c "import secrets; '
                'print(secrets.token_urlsafe(64))"'
            )
        # Em desenvolvimento geramos uma chave efêmera para não travar o boot.
        settings.SECRET_KEY = secrets.token_urlsafe(64)
        warnings.warn(
            "SECRET_KEY não definida: usando chave aleatória temporária. "
            "Todos os tokens serão invalidados ao reiniciar o servidor.",
            RuntimeWarning,
            stacklevel=2,
        )

    return settings


settings = get_settings()
