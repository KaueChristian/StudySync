"""
Modelos ORM da aplicação.

Este módulo reexporta todos os modelos para que `Base.metadata` esteja
completamente populada ao ser importado — condição necessária tanto para o
`create_all()` quanto para o autogenerate do Alembic.
"""

from app.models.note import Note, note_tags
from app.models.notification import Notification
from app.models.schedule import Schedule, ScheduleStatus
from app.models.search_result import SearchResult
from app.models.subject import Subject
from app.models.tag import Tag
from app.models.token import RefreshToken
from app.models.user import User

__all__ = [
    "Note",
    "Notification",
    "RefreshToken",
    "Schedule",
    "ScheduleStatus",
    "SearchResult",
    "Subject",
    "Tag",
    "User",
    "note_tags",
]
