"""Schemas Pydantic — contratos de entrada e saída da API."""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenPair,
    TokenRefreshResponse,
)
from app.schemas.common import Message, PaginatedResponse
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.schemas.notification import NotificationRead
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleRead,
    ScheduleStatusUpdate,
    ScheduleUpdate,
)
from app.schemas.search import (
    SaveSearchResultRequest,
    SearchQuery,
    SearchResponse,
    SearchResultItem,
    SearchResultRead,
)
from app.schemas.subject import SubjectCreate, SubjectRead, SubjectUpdate
from app.schemas.tag import TagRead
from app.schemas.user import PasswordChange, UserCreate, UserRead, UserUpdate

__all__ = [
    "LoginRequest",
    "Message",
    "NoteCreate",
    "NoteRead",
    "NoteUpdate",
    "NotificationRead",
    "PaginatedResponse",
    "PasswordChange",
    "RefreshRequest",
    "SaveSearchResultRequest",
    "ScheduleCreate",
    "ScheduleRead",
    "ScheduleStatusUpdate",
    "ScheduleUpdate",
    "SearchQuery",
    "SearchResponse",
    "SearchResultItem",
    "SearchResultRead",
    "SubjectCreate",
    "SubjectRead",
    "SubjectUpdate",
    "TagRead",
    "TokenPair",
    "TokenRefreshResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
