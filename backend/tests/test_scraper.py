"""
Motor de busca: funções puras (sempre) e provedores reais (opcional).

Os testes ao vivo tocam a internet e dependem de DuckDuckGo/Bing/Wikipédia
estarem respondendo — por isso só rodam com `STUDYSYNC_LIVE=1`:

    set STUDYSYNC_LIVE=1 && venv\\Scripts\\python.exe -m pytest tests/test_scraper.py
"""

from __future__ import annotations

import asyncio
import base64
import os

import httpx
import pytest

from app.services import scraper
from app.services.scraper import (
    RawResult,
    build_query,
    clean_bing_redirect,
    clean_ddg_redirect,
    dedupe_and_rank,
    normalize_url,
    tokenize,
)

live = pytest.mark.skipif(os.environ.get("STUDYSYNC_LIVE") != "1", reason="teste ao vivo")


def test_bing_redirect_is_unwrapped():
    target = "https://pt.khanacademy.org/science/biology"
    encoded = "a1" + base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
    wrapped = f"https://www.bing.com/ck/a?!&&p=abc&u={encoded}&ntb=1"
    assert clean_bing_redirect(wrapped) == target
    assert clean_bing_redirect("https://example.com/x") == "https://example.com/x"


def test_ddg_redirect_is_unwrapped():
    wrapped = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa%3Fb%3D1&rut=x"
    assert clean_ddg_redirect(wrapped) == "https://example.com/a?b=1"


def test_normalize_url():
    assert normalize_url("https://Example.com/a/?utm_source=x&q=a b c&fbclid=1#frag") == \
        "https://example.com/a?q=a+b+c"
    assert normalize_url("javascript:alert(1)") is None
    assert normalize_url("ftp://example.com") is None


def test_tokenize_keeps_short_meaningful_terms():
    assert tokenize("escala de pH") == {"escala", "ph"}
    assert {"ia", "3d"} <= tokenize("estudos de IA e 3D")


def test_build_query_adds_subject_only_when_missing():
    assert build_query("  célula   animal ", "Biologia") == "célula animal Biologia"
    assert build_query("célula biologia", "Biologia") == "célula biologia"


def _raw(url, title="Fotossíntese nas plantas", position=0):
    return RawResult(title=title, url=url, snippet="fotossíntese", position=position)


def test_ranking_caps_per_domain_after_scoring():
    raw = [_raw(f"https://a.com/{i}", title=f"Página {i} qualquer", position=i) for i in range(3)]
    raw.append(_raw("https://a.com/best", title="Fotossíntese nas plantas", position=9))
    ranked = dedupe_and_rank(raw, "fotossíntese plantas", limit=5)
    assert ranked[0].url == "https://a.com/best"
    assert len([r for r in ranked if r.source == "a.com"]) == 2


def test_ranking_drops_search_engine_links_and_duplicates():
    raw = [_raw("https://duckduckgo.com/y.js?ad=1"), _raw("https://example.com/a/"),
           _raw("https://example.com/a")]
    assert [r.url for r in dedupe_and_rank(raw, "fotossíntese", limit=5)] == ["https://example.com/a"]


def test_wikipedia_links_survive_titles_with_reserved_characters(monkeypatch):
    """Regressão: título com "?" ou "%" virava parte da query/escape inválido na URL."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": {"search": [
            {"title": "Quem Quer Ser um Milionário?", "snippet": "programa"},
            {"title": "100% Cotton", "snippet": "álbum"},
        ]}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await scraper._fetch_wikipedia(client, "milionário")

    results = asyncio.run(run())
    urls = [normalize_url(r.url) for r in results]
    assert urls == [
        "https://pt.wikipedia.org/wiki/Quem_Quer_Ser_um_Milionário%3F",
        "https://pt.wikipedia.org/wiki/100%25_Cotton",
    ]


@live
@pytest.mark.parametrize("provider", ["duckduckgo", "bing", "wikipedia"])
def test_live_provider_returns_real_links(provider):
    fetcher = dict(scraper.PROVIDERS)[provider]

    async def run():
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            return await fetcher(client, "fotossíntese")

    raw = asyncio.run(run())
    assert raw, f"{provider} não devolveu nada"
    for result in raw:
        assert result.url.startswith("http"), result.url
        assert "bing.com/ck/a" not in result.url


@live
def test_live_search_with_symbols_in_query():
    outcome = asyncio.run(scraper.search_content("C & C++ ponteiros", use_cache=False))
    assert 3 <= len(outcome.results) <= 5
    assert all(r.url.startswith("http") for r in outcome.results)
