"""
Rate limiting em memória (janela deslizante).

Aplicado às rotas de autenticação para mitigar ataques de força bruta e de
enumeração de credenciais, sem adicionar dependências externas (Redis etc.).

Limitação conhecida: o estado vive no processo. Em um deploy com múltiplos
workers, cada worker mantém sua própria contagem — para produção em escala,
troque por um backend compartilhado (Redis + slowapi).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings


class SlidingWindowRateLimiter:
    """Permite no máximo `max_requests` por `window_seconds` para cada chave."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """
        Registra uma tentativa.

        Returns:
            (permitido, segundos_para_liberar)
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._hits[key]
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
                return False, retry_after

            timestamps.append(now)

            # Evita crescimento indefinido do dicionário em processos longos.
            if len(self._hits) > 10_000:
                self._prune(cutoff)

            return True, 0

    def reset(self, key: str) -> None:
        """Zera o contador de uma chave (ex.: após um login bem-sucedido)."""
        with self._lock:
            self._hits.pop(key, None)

    def _prune(self, cutoff: float) -> None:
        """Remove chaves cujas janelas já expiraram. Chamado sob lock."""
        stale = [k for k, v in self._hits.items() if not v or v[-1] < cutoff]
        for key in stale:
            del self._hits[key]


auth_limiter = SlidingWindowRateLimiter(
    max_requests=settings.AUTH_RATE_LIMIT_MAX,
    window_seconds=settings.AUTH_RATE_LIMIT_WINDOW,
)


def client_ip(request: Request) -> str:
    """
    Resolve o IP do cliente.

    `X-Forwarded-For` só é confiável atrás de um proxy reverso controlado —
    por isso só é consultado quando a aplicação roda em produção.
    """
    if settings.is_production:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    """Dependência do FastAPI: bloqueia com HTTP 429 ao estourar o limite."""
    key = f"{client_ip(request)}:{request.url.path}"
    allowed, retry_after = auth_limiter.check(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Aguarde alguns instantes e tente novamente.",
            headers={"Retry-After": str(retry_after)},
        )
