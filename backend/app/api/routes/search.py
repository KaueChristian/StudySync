"""
Motor de busca de conteúdo de apoio.

Fluxo do usuário:
    1. `POST /api/search` — busca os 5 links mais relevantes sobre o tema.
    2. `POST /api/search/save` — anexa um dos links à anotação/agendamento.
    3. `GET  /api/search/saved` — consulta a biblioteca de links salvos.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.rate_limit import SlidingWindowRateLimiter, client_ip
from app.models.note import Note
from app.models.schedule import Schedule
from app.models.search_result import SearchResult
from app.schemas.common import Message
from app.schemas.search import (
    SaveSearchResultRequest,
    SearchQuery,
    SearchResponse,
    SearchResultItem,
    SearchResultRead,
)
from app.services.scraper import SearchEngineError, normalize_url, search_content

logger = logging.getLogger("studysync.search")

router = APIRouter()

# Limite dedicado: protege os provedores externos de rajadas de requisições.
search_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=60)


@router.post("", response_model=SearchResponse, summary="Buscar conteúdo de apoio")
async def search(
    payload: SearchQuery,
    request: Request,
    current_user: CurrentUser,
    refresh: Annotated[
        bool, Query(description="Ignora o cache e refaz a busca.")
    ] = False,
) -> SearchResponse:
    """
    Pesquisa na web os links mais relevantes sobre o tema informado.

    A busca percorre uma cascata de provedores (DuckDuckGo → Lite → Bing →
    Wikipédia) e ordena os resultados por relevância e confiabilidade da fonte.
    """
    allowed, retry_after = search_limiter.check(f"user:{current_user.id}")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas buscas em sequência. Aguarde alguns segundos.",
            headers={"Retry-After": str(retry_after)},
        )

    if not payload.query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe um tema para pesquisar.",
        )

    try:
        outcome = await search_content(
            payload.query,
            limit=payload.limit,
            subject_hint=payload.subject_hint,
            use_cache=not refresh,
        )
    except SearchEngineError as exc:
        logger.error("Busca falhou para %r: %s", payload.query, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    logger.info(
        "Busca de %s: %r → %d resultados via %s (ip=%s)",
        current_user.email,
        outcome.query,
        len(outcome.results),
        outcome.provider,
        client_ip(request),
    )

    return SearchResponse(
        query=outcome.query,
        provider=outcome.provider,
        cached=outcome.cached,
        took_ms=outcome.took_ms,
        results=[
            SearchResultItem(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                source=r.source,
                score=r.score,
            )
            for r in outcome.results
        ],
    )


@router.post(
    "/save",
    response_model=SearchResultRead,
    status_code=status.HTTP_201_CREATED,
    summary="Salvar link em anotação ou agendamento",
)
def save_result(
    payload: SaveSearchResultRequest, current_user: CurrentUser, db: DbSession
) -> SearchResultRead:
    """Anexa um link de apoio a uma anotação **ou** a um agendamento."""
    if (payload.note_id is None) == (payload.schedule_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe exatamente um destino: note_id ou schedule_id.",
        )

    # Titularidade do destino.
    if payload.note_id is not None:
        owns = db.scalar(
            select(Note.id).where(
                Note.id == payload.note_id, Note.owner_id == current_user.id
            )
        )
        if not owns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Anotação não encontrada."
            )
    else:
        owns = db.scalar(
            select(Schedule.id).where(
                Schedule.id == payload.schedule_id,
                Schedule.owner_id == current_user.id,
            )
        )
        if not owns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado.",
            )

    url = normalize_url(str(payload.url)) or str(payload.url).strip()

    # Idempotência: salvar o mesmo link duas vezes devolve o registro existente.
    duplicate = db.scalar(
        select(SearchResult).where(
            SearchResult.owner_id == current_user.id,
            SearchResult.url == url,
            SearchResult.note_id == payload.note_id,
            SearchResult.schedule_id == payload.schedule_id,
        )
    )
    if duplicate:
        return SearchResultRead.model_validate(duplicate)

    result = SearchResult(
        owner_id=current_user.id,
        note_id=payload.note_id,
        schedule_id=payload.schedule_id,
        title=payload.title,
        url=url,
        snippet=payload.snippet,
        source=payload.source,
        query=payload.query,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return SearchResultRead.model_validate(result)


@router.get(
    "/saved",
    response_model=list[SearchResultRead],
    summary="Listar todos os links salvos",
)
def list_saved(
    current_user: CurrentUser,
    db: DbSession,
    note_id: Annotated[int | None, Query()] = None,
    schedule_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[SearchResultRead]:
    """Biblioteca de links do usuário, opcionalmente filtrada pelo destino."""
    query = select(SearchResult).where(SearchResult.owner_id == current_user.id)

    if note_id is not None:
        query = query.where(SearchResult.note_id == note_id)
    if schedule_id is not None:
        query = query.where(SearchResult.schedule_id == schedule_id)

    results = db.scalars(
        query.order_by(SearchResult.created_at.desc()).limit(limit)
    ).all()
    return [SearchResultRead.model_validate(r) for r in results]


@router.delete(
    "/saved/{result_id}", response_model=Message, summary="Remover link salvo"
)
def delete_saved(
    result_id: int, current_user: CurrentUser, db: DbSession
) -> Message:
    result = db.scalar(
        select(SearchResult).where(
            SearchResult.id == result_id, SearchResult.owner_id == current_user.id
        )
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link não encontrado."
        )

    db.delete(result)
    db.commit()
    return Message(detail="Link removido com sucesso.")
