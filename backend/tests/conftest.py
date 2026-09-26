"""
Base da suíte: um banco SQLite descartável, criado pelas migrations do boot
(o mesmo caminho do app real), e um cliente HTTP contra a aplicação inteira.

    cd backend
    venv\\Scripts\\python.exe -m pytest

O ambiente precisa ser definido antes de qualquer import de `app`: as
configurações e o engine do banco são criados no import.
"""

from __future__ import annotations

import itertools
import os
import shutil
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="studysync-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["ENV"] = "test"
os.environ["SECRET_KEY"] = "chave-de-teste-" + "x" * 48
os.environ["FRONTEND_DIST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main_module  # noqa: E402
from app.api.routes.search import search_limiter  # noqa: E402
from app.core.rate_limit import auth_limiter  # noqa: E402
from app.db.session import engine  # noqa: E402

# O agendador roda numa thread própria e dispararia lembretes no meio dos
# testes. Os testes de lembrete chamam `scan_reminders()` diretamente.
main_module.start_scheduler = lambda: None

PASSWORD = "Estudo2024"
_counter = itertools.count(1)


@pytest.fixture(scope="session")
def client():
    with TestClient(main_module.app) as test_client:
        yield test_client
    engine.dispose()
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    auth_limiter._hits.clear()
    search_limiter._hits.clear()
    yield


class User:
    """Usuário cadastrado pela API, com os cabeçalhos prontos para uso."""

    def __init__(self, data: dict):
        self.data = data
        self.id = data["user"]["id"]
        self.email = data["user"]["email"]
        self.access = data["access_token"]
        self.refresh = data["refresh_token"]
        self.headers = {"Authorization": f"Bearer {self.access}"}


@pytest.fixture
def make_user(client):
    def factory(timezone: str = "America/Sao_Paulo") -> User:
        n = next(_counter)
        response = client.post(
            "/api/auth/register",
            json={
                "name": f"Usuária {n}",
                "email": f"user{n}@example.com",
                "password": PASSWORD,
                "timezone": timezone,
            },
        )
        assert response.status_code == 201, response.text
        return User(response.json())

    return factory


@pytest.fixture
def user(make_user) -> User:
    return make_user()
