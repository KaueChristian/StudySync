"""
Gerenciador de conexões WebSocket — entrega de notificações em tempo real.

Um mesmo usuário pode ter várias abas abertas, por isso o mapa é
`user_id -> set[WebSocket]`. A emissão é *best-effort*: conexões mortas são
descartadas silenciosamente, já que a notificação também fica persistida no
banco e será exibida no próximo carregamento.

Ponte thread → event loop
-------------------------
O APScheduler roda em uma thread separada, mas `websocket.send_json` só pode
ser aguardado dentro do event loop do asyncio. `broadcast_threadsafe` resolve
isso agendando a corrotina no loop principal, capturado no startup.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("studysync.notifier")


class ConnectionManager:
    """Registro das conexões WebSocket ativas, indexadas por usuário."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    # ------------------------------------------------------------- ciclo
    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Guarda o event loop principal (chamado no startup da aplicação)."""
        self._loop = loop

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Aceita a conexão e a registra."""
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
        logger.info(
            "WebSocket conectado (user_id=%s, conexões=%d)",
            user_id,
            len(self._connections.get(user_id, ())),
        )

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove a conexão do registro."""
        async with self._lock:
            sockets = self._connections.get(user_id)
            if sockets:
                sockets.discard(websocket)
                if not sockets:
                    self._connections.pop(user_id, None)
        logger.info("WebSocket desconectado (user_id=%s)", user_id)

    # ------------------------------------------------------------- envio
    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> int:
        """
        Envia um payload JSON para todas as conexões do usuário.

        Returns:
            Quantidade de conexões que receberam a mensagem.
        """
        async with self._lock:
            sockets = list(self._connections.get(user_id, ()))

        if not sockets:
            return 0

        delivered = 0
        dead: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(payload)
                delivered += 1
            except Exception:  # conexão caiu entre o snapshot e o envio
                dead.append(socket)

        for socket in dead:
            await self.disconnect(user_id, socket)

        return delivered

    def send_to_user_threadsafe(self, user_id: int, payload: dict[str, Any]) -> None:
        """
        Versão chamável de fora do event loop (ex.: job do APScheduler).

        Se o loop ainda não estiver disponível, a mensagem é descartada — a
        notificação persistida no banco cobre esse caso.
        """
        if self._loop is None or self._loop.is_closed():
            logger.debug("Event loop indisponível; notificação apenas persistida.")
            return
        asyncio.run_coroutine_threadsafe(
            self.send_to_user(user_id, payload), self._loop
        )

    # ------------------------------------------------------------ estado
    def is_online(self, user_id: int) -> bool:
        """Indica se o usuário possui ao menos uma conexão ativa."""
        return bool(self._connections.get(user_id))

    @property
    def total_connections(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())


# Instância única compartilhada por toda a aplicação.
manager = ConnectionManager()
