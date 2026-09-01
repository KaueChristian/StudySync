"""Agregador de todos os roteadores da API."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    notes,
    notifications,
    schedules,
    search,
    subjects,
    tags,
    ws,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["Matérias"])
api_router.include_router(notes.router, prefix="/notes", tags=["Anotações"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Agendamentos"])
api_router.include_router(search.router, prefix="/search", tags=["Busca de conteúdo"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notificações"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(ws.router, tags=["WebSocket"])
