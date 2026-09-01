"""
Popula o banco com dados de demonstração.

Uso (a partir de /backend, com o venv ativado):
    python -m app.seed

Cria o usuário `demo@studysync.dev` (senha `Estudo2024`) com matérias,
anotações e sessões de estudo — uma delas propositalmente agendada para daqui
a poucos minutos, para você ver o lembrete em tempo real disparar.

O script é idempotente: rodar duas vezes não duplica os dados.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.models.note import Note
from app.models.schedule import Schedule, ScheduleStatus
from app.models.search_result import SearchResult
from app.models.subject import Subject
from app.models.user import User
from app.core.security import hash_password
from app.services.scheduler import compute_remind_at
from app.services.tags import resolve_tags

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s | %(message)s")
logger = logging.getLogger("studysync.seed")

DEMO_EMAIL = "demo@studysync.dev"
DEMO_PASSWORD = "Estudo2024"

SUBJECTS = [
    {
        "name": "Biologia",
        "description": "Citologia, anatomia humana, genética e ecologia.",
        "color": "#22c55e",
        "icon": "leaf",
    },
    {
        "name": "Matemática",
        "description": "Álgebra, geometria analítica e funções.",
        "color": "#3b82f6",
        "icon": "calculator",
    },
    {
        "name": "História",
        "description": "Brasil República, Idade Moderna e Guerra Fria.",
        "color": "#f59e0b",
        "icon": "landmark",
    },
    {
        "name": "Química",
        "description": "Química orgânica, estequiometria e ligações.",
        "color": "#a855f7",
        "icon": "flask-conical",
    },
]

NOTES = [
    {
        "subject": "Biologia",
        "title": "Partes do corpo humano — sistemas",
        "category": "Resumo",
        "tags": ["anatomia", "prova", "sistemas"],
        "content": """# Sistemas do corpo humano

O corpo humano é organizado em **11 sistemas** que atuam de forma integrada.

## Principais sistemas

| Sistema | Função central | Órgãos-chave |
|---|---|---|
| Circulatório | Transporte de gases e nutrientes | Coração, artérias, veias |
| Respiratório | Trocas gasosas | Pulmões, traqueia, diafragma |
| Digestório | Quebra e absorção de nutrientes | Estômago, intestinos, fígado |
| Nervoso | Coordenação e resposta a estímulos | Encéfalo, medula, nervos |
| Esquelético | Sustentação e proteção | 206 ossos |

## Pontos que sempre caem em prova

1. O coração possui **4 câmaras**: dois átrios e dois ventrículos.
2. A hematose (troca gasosa) acontece nos **alvéolos pulmonares**.
3. O intestino delgado é onde ocorre a **maior parte da absorção**.

> Revisar o trajeto completo da pequena e da grande circulação.

- [ ] Refazer o esquema do sistema circulatório
- [x] Ler o capítulo 12 do livro
""",
    },
    {
        "subject": "Matemática",
        "title": "Funções do 2º grau",
        "category": "Fórmulas",
        "tags": ["álgebra", "fórmulas"],
        "content": """# Função quadrática

Forma geral: `f(x) = ax² + bx + c`, com `a ≠ 0`.

## Raízes (Bhaskara)

```
Δ = b² - 4ac
x = (-b ± √Δ) / 2a
```

## Análise do discriminante

- `Δ > 0` → duas raízes reais distintas
- `Δ = 0` → uma raiz real (dupla)
- `Δ < 0` → nenhuma raiz real

## Vértice da parábola

`Xv = -b / 2a` e `Yv = -Δ / 4a`

Se `a > 0` a concavidade é **para cima** (ponto de mínimo);
se `a < 0`, **para baixo** (ponto de máximo).
""",
    },
    {
        "subject": "História",
        "title": "Guerra Fria — linha do tempo",
        "category": "Revisão",
        "tags": ["século xx", "prova"],
        "content": """# Guerra Fria (1947 – 1991)

Disputa geopolítica e ideológica entre **EUA** (capitalismo) e
**URSS** (socialismo), sem confronto militar direto entre as potências.

## Marcos

- **1947** — Doutrina Truman e Plano Marshall
- **1949** — Criação da OTAN
- **1955** — Pacto de Varsóvia
- **1961** — Construção do Muro de Berlim
- **1962** — Crise dos Mísseis de Cuba
- **1989** — Queda do Muro de Berlim
- **1991** — Dissolução da União Soviética

## Conceitos-chave

**Corrida armamentista**, **corrida espacial**, **política de contenção** e
**coexistência pacífica**.
""",
    },
    {
        "subject": "Química",
        "title": "Ligações químicas",
        "category": "Resumo",
        "tags": ["ligações", "revisão"],
        "content": """# Tipos de ligação química

## Iônica
Transferência de elétrons entre metal e ametal.
Ex.: `NaCl` — sólido, alto ponto de fusão, conduz corrente quando dissolvido.

## Covalente
Compartilhamento de pares de elétrons entre ametais.
Ex.: `H₂O`, `CO₂`.

## Metálica
"Mar de elétrons" deslocalizados entre cátions metálicos — explica a
condutividade e a maleabilidade dos metais.
""",
    },
]


def _seed_user(db) -> User:
    """Cria (ou recupera) o usuário de demonstração."""
    user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user:
        logger.info("Usuário demo já existe (id=%s).", user.id)
        return user

    user = User(
        name="Estudante Demo",
        email=DEMO_EMAIL,
        hashed_password=hash_password(DEMO_PASSWORD),
        timezone="America/Sao_Paulo",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Usuário demo criado (id=%s).", user.id)
    return user


def _seed_subjects(db, user: User) -> dict[str, Subject]:
    """Cria as matérias de demonstração."""
    result: dict[str, Subject] = {}
    for data in SUBJECTS:
        subject = db.scalar(
            select(Subject).where(
                Subject.owner_id == user.id, Subject.name == data["name"]
            )
        )
        if subject is None:
            subject = Subject(owner_id=user.id, **data)
            db.add(subject)
            db.commit()
            db.refresh(subject)
        result[data["name"]] = subject

    logger.info("Matérias disponíveis: %d", len(result))
    return result


def _seed_notes(db, user: User, subjects: dict[str, Subject]) -> list[Note]:
    """Cria as anotações de demonstração."""
    created: list[Note] = []
    for data in NOTES:
        existing = db.scalar(
            select(Note).where(Note.owner_id == user.id, Note.title == data["title"])
        )
        if existing:
            created.append(existing)
            continue

        note = Note(
            owner_id=user.id,
            subject_id=subjects[data["subject"]].id,
            title=data["title"],
            content=data["content"],
            category=data["category"],
        )
        note.tags = resolve_tags(db, user.id, data["tags"])
        db.add(note)
        db.commit()
        db.refresh(note)
        created.append(note)

    logger.info("Anotações disponíveis: %d", len(created))
    return created


def _seed_schedules(db, user: User, subjects: dict[str, Subject]) -> None:
    """Cria as sessões de estudo, incluindo uma prestes a disparar lembrete."""
    now = datetime.now(timezone.utc)

    plan = [
        {
            "subject": "Biologia",
            "title": "Revisão de anatomia",
            "topic": "Partes do corpo humano",
            "description": "Focar nos sistemas circulatório e respiratório.",
            "location": "Biblioteca central",
            # Daqui a ~18 min, com lembrete de 15 min → dispara em ~3 min.
            "start_offset": timedelta(minutes=18),
            "duration": timedelta(minutes=90),
            "remind_minutes": 15,
            "status": ScheduleStatus.PENDING,
        },
        {
            "subject": "Matemática",
            "title": "Lista de exercícios — funções",
            "topic": "Função do 2º grau e gráficos",
            "location": "Em casa",
            "start_offset": timedelta(days=1, hours=2),
            "duration": timedelta(minutes=120),
            "remind_minutes": 30,
            "status": ScheduleStatus.PENDING,
        },
        {
            "subject": "História",
            "title": "Leitura dirigida",
            "topic": "Crise dos Mísseis de Cuba",
            "location": "Sala de estudos",
            "start_offset": timedelta(days=2, hours=4),
            "duration": timedelta(minutes=60),
            "remind_minutes": 15,
            "status": ScheduleStatus.PENDING,
        },
        {
            "subject": "Química",
            "title": "Resolução de estequiometria",
            "topic": "Cálculos estequiométricos",
            "start_offset": timedelta(days=-2),
            "duration": timedelta(minutes=75),
            "remind_minutes": 15,
            "status": ScheduleStatus.COMPLETED,
        },
        {
            "subject": "Biologia",
            "title": "Videoaula de genética",
            "topic": "Leis de Mendel",
            "start_offset": timedelta(days=-1, hours=-3),
            "duration": timedelta(minutes=45),
            "remind_minutes": 15,
            "status": ScheduleStatus.COMPLETED,
        },
    ]

    count = 0
    for item in plan:
        exists = db.scalar(
            select(Schedule).where(
                Schedule.owner_id == user.id, Schedule.title == item["title"]
            )
        )
        if exists:
            continue

        start_at = now + item["start_offset"]
        schedule = Schedule(
            owner_id=user.id,
            subject_id=subjects[item["subject"]].id,
            title=item["title"],
            topic=item.get("topic"),
            description=item.get("description"),
            location=item.get("location"),
            start_at=start_at,
            end_at=start_at + item["duration"],
            remind_minutes=item["remind_minutes"],
            reminder_enabled=True,
            status=item["status"],
        )
        schedule.remind_at = compute_remind_at(
            start_at, item["remind_minutes"], True
        )
        # Sessões passadas ou já concluídas não devem gerar alerta retroativo.
        schedule.reminder_sent = (
            item["status"] != ScheduleStatus.PENDING
            or (schedule.remind_at is not None and schedule.remind_at < now)
        )

        db.add(schedule)
        count += 1

    db.commit()
    logger.info("Novas sessões de estudo criadas: %d", count)


def _seed_links(db, user: User, notes: list[Note]) -> None:
    """Anexa alguns links de apoio de exemplo à primeira anotação."""
    if not notes:
        return

    target = notes[0]
    samples = [
        {
            "title": "Corpo humano — Wikipédia",
            "url": "https://pt.wikipedia.org/wiki/Corpo_humano",
            "snippet": (
                "O corpo humano é a estrutura física de um ser humano, "
                "composta por sistemas de órgãos integrados."
            ),
            "source": "pt.wikipedia.org",
        },
        {
            "title": "Sistema circulatório — Mundo Educação",
            "url": "https://mundoeducacao.uol.com.br/biologia/sistema-circulatorio.htm",
            "snippet": (
                "O sistema circulatório é responsável pelo transporte de "
                "sangue, nutrientes, gases e hormônios pelo corpo."
            ),
            "source": "mundoeducacao.uol.com.br",
        },
    ]

    added = 0
    for sample in samples:
        exists = db.scalar(
            select(SearchResult).where(
                SearchResult.owner_id == user.id,
                SearchResult.note_id == target.id,
                SearchResult.url == sample["url"],
            )
        )
        if exists:
            continue

        db.add(
            SearchResult(
                owner_id=user.id,
                note_id=target.id,
                query="partes do corpo humano",
                **sample,
            )
        )
        added += 1

    db.commit()
    logger.info("Links de apoio adicionados: %d", added)


def seed() -> None:
    """Executa toda a rotina de população."""
    init_database()

    with SessionLocal() as db:
        user = _seed_user(db)
        subjects = _seed_subjects(db, user)
        notes = _seed_notes(db, user, subjects)
        _seed_schedules(db, user, subjects)
        _seed_links(db, user, notes)

    print()
    print("=" * 64)
    print("  Dados de demonstração prontos!")
    print(f"  E-mail : {DEMO_EMAIL}")
    print(f"  Senha  : {DEMO_PASSWORD}")
    print()
    print("  A sessão 'Revisão de anatomia' começa em ~18 minutos e o")
    print("  lembrete (15 min antes) dispara em cerca de 3 minutos —")
    print("  deixe a aplicação aberta para ver a notificação chegar.")
    print("=" * 64)


if __name__ == "__main__":
    seed()
