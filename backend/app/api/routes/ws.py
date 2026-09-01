"""
Canal WebSocket de notificações em tempo real.

Endpoint: `ws://localhost:8000/api/ws/notifications?token=<access_token>`

Protocolo (mensagens JSON do servidor):
    {"event": "connected",    "data": {...}}   → handshake aceito
    {"event": "notification", "data": {...}}   → lembrete disparado
    {"event": "pong",         "data": {...}}   → resposta ao heartbeat

O cliente envia apenas `{"event": "ping"}` como heartbeat; qualquer outra
mensagem é ignorada — o canal é intencionalmente unidirecional para escrita.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from app.core.deps import authenticate_websocket
from app.services.notifier import manager

logger = logging.getLogger("studysync.ws")

router = APIRouter()


@router.websocket("/ws/notifications")
async def notifications_socket(
    websocket: WebSocket,
    user_id: Annotated[int, Depends(authenticate_websocket)],
) -> None:
    """Mantém a conexão aberta e entrega os lembretes assim que são gerados."""
    await manager.connect(user_id, websocket)

    try:
        await websocket.send_json(
            {
                "event": "connected",
                "data": {
                    "user_id": user_id,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

        while True:
            # `receive_json` também detecta o fechamento da conexão.
            message = await websocket.receive_json()
            if isinstance(message, dict) and message.get("event") == "ping":
                await websocket.send_json(
                    {
                        "event": "pong",
                        "data": {"server_time": datetime.now(timezone.utc).isoformat()},
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 — payload malformado não deve vazar stack
        logger.debug("WebSocket encerrado com erro (user_id=%s)", user_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except RuntimeError:
            pass
    finally:
        await manager.disconnect(user_id, websocket)
