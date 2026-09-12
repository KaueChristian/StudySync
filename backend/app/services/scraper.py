"""
Motor de busca de conteúdo de apoio (web scraping, sem custo de API).

Arquitetura em cascata
----------------------
A busca tenta os provedores em ordem e devolve o primeiro que retornar
resultados úteis. Se um provedor mudar o HTML ou aplicar bloqueio, os demais
mantêm a funcionalidade viva:

    1. DuckDuckGo HTML   (html.duckduckgo.com/html/)   — melhor cobertura
    2. DuckDuckGo Lite   (lite.duckduckgo.com/lite/)   — HTML mínimo, estável
    3. Bing              (www.bing.com/search)         — provedor alternativo
    4. Wikipedia API     (pt.wikipedia.org/w/api.php)  — JSON oficial, garante
                                                         resposta didática

Pós-processamento
-----------------
Os resultados brutos passam por normalização de URL, deduplicação por domínio+
caminho, e um **ranking de relevância e confiabilidade** que privilegia fontes
acadêmicas/educacionais e a aderência da página ao termo pesquisado.

Boas práticas de scraping adotadas: User-Agent identificável, timeout curto,
cache em memória (evita repetir a mesma consulta) e limite de concorrência.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger("studysync.scraper")

# Pool pequeno de User-Agents realistas (navegadores/SOs comuns). Alternar
# entre eles evita a impressão digital estática de "sempre o mesmo cliente",
# um dos sinais mais óbvios de scraping automatizado.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 "
    "Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
]


def _browser_headers(referer: str) -> dict[str, str]:
    """
    Monta um conjunto de cabeçalhos parecido com o de um navegador real
    **navegando** (não chamando uma API) — usado pelos três buscadores, que
    servem HTML e usam esses sinais de navegação pra detectar automação.

    User-Agent sorteado a cada requisição + os cabeçalhos `Sec-Fetch-*` que
    um navegador sempre envia e um cliente HTTP simples não; `referer`
    coerente com o site de destino (chegar no Bing "vindo" do DuckDuckGo,
    por exemplo, é uma inconsistência que também pesa contra o pedido).
    """
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        # Não anunciar "br" (brotli) sem httpx[brotli] instalado; do contrário
        # o buscador responde em brotli, httpx devolve bytes crus e o parser falha.
        "Accept-Encoding": "gzip, deflate",
        "Referer": referer,
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "no-cache",
    }


def _wikipedia_headers() -> dict[str, str]:
    """
    Cabeçalhos pra API da Wikipédia — deliberadamente diferentes dos usados
    contra os buscadores.

    A API do MediaWiki não é uma parede anti-bot: é feita pra ser chamada
    programaticamente, e a própria Wikimedia recomenda um User-Agent honesto
    e descritivo em vez de imitar um navegador (política em
    https://meta.wikimedia.org/wiki/User-Agent_policy). Fingir uma navegação
    de página completa (`Sec-Fetch-Dest: document`) numa chamada de API JSON
    é, na prática, um sinal *mais* suspeito, não menos — foi exatamente isso
    que causava um 403 aqui antes desta separação.
    """
    return {
        "User-Agent": (
            "StudySync/1.0 (https://github.com/KaueChristian/StudySync; "
            "projeto educacional de agendamento de estudos) httpx"
        ),
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

# ---------------------------------------------------------------------------
# Heurísticas de confiabilidade
# ---------------------------------------------------------------------------

# Domínios/sufixos com peso extra: instituições de ensino, órgãos públicos e
# portais educacionais consolidados.
TRUSTED_PATTERNS: dict[str, float] = {
    r"\.edu(\.[a-z]{2})?$": 22.0,
    r"\.gov(\.[a-z]{2})?$": 22.0,
    r"\.ac\.[a-z]{2}$": 20.0,
    r"(^|\.)usp\.br$": 20.0,
    r"(^|\.)unicamp\.br$": 20.0,
    r"(^|\.)ufmg\.br$": 18.0,
    r"(^|\.)fiocruz\.br$": 20.0,
    r"(^|\.)scielo\.": 20.0,
    r"(^|\.)pubmed\.ncbi\.nlm\.nih\.gov$": 22.0,
    r"(^|\.)wikipedia\.org$": 16.0,
    r"(^|\.)khanacademy\.org$": 16.0,
    r"(^|\.)britannica\.com$": 14.0,
    r"(^|\.)mundoeducacao\.uol\.com\.br$": 12.0,
    r"(^|\.)brasilescola\.uol\.com\.br$": 12.0,
    r"(^|\.)todamateria\.com\.br$": 11.0,
    r"(^|\.)infoescola\.com$": 10.0,
    r"(^|\.)educacao\.uol\.com\.br$": 10.0,
    r"(^|\.)stoodi\.com\.br$": 9.0,
    r"(^|\.)preparaenem\.com$": 9.0,
    r"(^|\.)nature\.com$": 16.0,
    r"(^|\.)sciencedirect\.com$": 14.0,
    r"(^|\.)researchgate\.net$": 10.0,
    r"(^|\.)github\.io$": 6.0,
    r"(^|\.)medium\.com$": 3.0,
}

# Domínios penalizados: agregadores, redes sociais e conteúdo pago/efêmero.
PENALIZED_PATTERNS: dict[str, float] = {
    r"(^|\.)pinterest\.": -25.0,
    r"(^|\.)facebook\.com$": -30.0,
    r"(^|\.)instagram\.com$": -30.0,
    r"(^|\.)x\.com$": -25.0,
    r"(^|\.)twitter\.com$": -25.0,
    r"(^|\.)tiktok\.com$": -30.0,
    r"(^|\.)passeidireto\.com$": -20.0,
    r"(^|\.)studocu\.com$": -20.0,
    r"(^|\.)brainly\.com\.br$": -18.0,
    r"(^|\.)docsity\.com$": -18.0,
    r"(^|\.)slideshare\.net$": -10.0,
    r"(^|\.)youtube\.com$": -4.0,
    r"(^|\.)amazon\.": -30.0,
    r"(^|\.)mercadolivre\.": -35.0,
    r"(^|\.)shopee\.": -35.0,
}

# Parâmetros de rastreamento removidos ao normalizar a URL.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "rut", "_ga",
}

STOPWORDS = {
    "a", "as", "ao", "aos", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "na", "nas", "no", "nos", "o", "os", "ou", "para", "pelo",
    "por", "que", "se", "sobre", "um", "uma", "estudo", "estudar", "the",
    "of", "and", "for", "to", "in", "on",
}


# ---------------------------------------------------------------------------
# Estruturas
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class RawResult:
    """Resultado bruto extraído de um provedor, antes do ranking."""

    title: str
    url: str
    snippet: str | None = None
    position: int = 0
    score: float = 0.0
    source: str = field(default="")


@dataclass(slots=True)
class SearchOutcome:
    """Resultado final da busca, já ordenado."""

    query: str
    provider: str
    results: list[RawResult]
    cached: bool = False
    took_ms: int = 0


class SearchEngineError(RuntimeError):
    """Nenhum provedor conseguiu responder à consulta."""


class BlockedByProviderError(RuntimeError):
    """O provedor detectou a requisição como automatizada e bloqueou/desafiou."""


def _raise_if_blocked(provider_name: str, response: httpx.Response) -> None:
    """
    Detecta bloqueio/desafio anti-bot que não aparece como erro HTTP comum.

    O DuckDuckGo, por exemplo, responde **202** com uma página de "checando
    seu navegador" em vez de um 4xx/5xx — `raise_for_status()` não pega isso,
    e sem esta checagem o provedor pareceria apenas "sem resultados" em vez de
    "bloqueado", o que confunde o diagnóstico e não alimenta o disjuntor de
    circuito (`ProviderHealth`) que evita insistir num provedor já bloqueado.
    """
    response.raise_for_status()
    if response.status_code == 202:
        raise BlockedByProviderError(
            f"{provider_name} devolveu 202 (provável desafio anti-bot)"
        )


# ---------------------------------------------------------------------------
# Cache TTL em memória
# ---------------------------------------------------------------------------
class TTLCache:
    """Cache simples com expiração — evita repetir buscas idênticas."""

    def __init__(self, ttl: int, max_size: int = 256) -> None:
        self.ttl = ttl
        self.max_size = max_size
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            stored_at, value = entry
            if time.monotonic() - stored_at > self.ttl:
                self._data.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if len(self._data) >= self.max_size:
                # Descarta a entrada mais antiga (FIFO aproximado).
                oldest = min(self._data.items(), key=lambda kv: kv[1][0])[0]
                self._data.pop(oldest, None)
            self._data[key] = (time.monotonic(), value)

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()


_cache = TTLCache(ttl=settings.SCRAPER_CACHE_TTL)

# Evita que várias buscas simultâneas saturem os provedores.
_semaphore = asyncio.Semaphore(4)


class ProviderHealth:
    """
    Disjuntor de circuito simples por provedor.

    Sem isso, um provedor bloqueado (ex.: DuckDuckGo devolvendo um desafio
    anti-bot) seria tentado do zero em **toda** busca — desperdiçando tempo
    de resposta e, pior, mantendo o tráfego repetitivo que motivou o bloqueio
    em primeiro lugar. Depois de `threshold` falhas seguidas, o provedor fica
    em "cooldown" por um tempo e as buscas pulam direto para o próximo da
    cascata; passado o cooldown, ele volta a ser tentado normalmente (sem
    intervenção manual).
    """

    def __init__(self, threshold: int = 2, cooldown: float = 600.0) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures: dict[str, int] = {}
        self._blocked_until: dict[str, float] = {}

    def is_available(self, name: str) -> bool:
        until = self._blocked_until.get(name)
        return until is None or time.monotonic() >= until

    def record_success(self, name: str) -> None:
        self._failures.pop(name, None)
        self._blocked_until.pop(name, None)

    def record_failure(self, name: str) -> None:
        count = self._failures.get(name, 0) + 1
        self._failures[name] = count
        if count >= self.threshold:
            self._blocked_until[name] = time.monotonic() + self.cooldown
            logger.warning(
                "Provedor %s em cooldown por %.0fs após %d falhas seguidas",
                name,
                self.cooldown,
                count,
            )


_health = ProviderHealth()


# ---------------------------------------------------------------------------
# Utilitários de texto e URL
# ---------------------------------------------------------------------------
def strip_accents(text: str) -> str:
    """Remove acentuação para comparações tolerantes."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def tokenize(text: str) -> set[str]:
    """Extrai os termos significativos de uma frase."""
    words = re.findall(r"[a-z0-9]+", strip_accents(text.lower()))
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def clean_ddg_redirect(url: str) -> str:
    """
    Extrai a URL real de um link de redirecionamento do DuckDuckGo.

    O DDG entrega `//duckduckgo.com/l/?uddg=<url-encoded>&rut=...`.
    """
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg")
        if target:
            return target[0]
    return url


def clean_bing_redirect(url: str) -> str:
    """
    Extrai a URL real de um link de rastreamento de clique do Bing.

    O Bing envolve resultados orgânicos em `bing.com/ck/a?...&u=a1<base64>`.
    Sem desembrulhar isso, todo resultado "vira" o domínio `bing.com` aos
    olhos do ranking — o que disparava o limite de 2 links por domínio do
    `dedupe_and_rank` e travava a busca em só 2 resultados (todos URLs de
    redirecionamento que não abrem direito fora de uma sessão do Bing).
    """
    parsed = urlparse(url)
    if "bing.com" not in parsed.netloc or not parsed.path.startswith("/ck/a"):
        return url

    encoded = parse_qs(parsed.query).get("u")
    if not encoded:
        return url

    value = encoded[0]
    # O prefixo "a1" marca o esquema de codificação (base64); outros
    # prefixos não documentados são deixados como estão.
    if not value.startswith("a1"):
        return url
    value = value[2:]

    padded = value + "=" * (-len(value) % 4)
    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            decoded = decoder(padded).decode("utf-8")
        except Exception:  # noqa: BLE001 — tenta o próximo esquema
            continue
        if decoded.startswith(("http://", "https://")):
            return decoded
    return url


def normalize_url(url: str) -> str | None:
    """Valida o esquema, remove parâmetros de rastreamento e o fragmento."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    kept = {
        k: v
        for k, v in parse_qs(parsed.query).items()
        if k.lower() not in TRACKING_PARAMS
    }
    query = "&".join(f"{k}={v[0]}" for k, v in sorted(kept.items()) if v)
    path = parsed.path.rstrip("/") or "/"

    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", query, ""))


def domain_of(url: str) -> str:
    """Domínio da URL, sem o prefixo `www.`."""
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


# ---------------------------------------------------------------------------
# Provedores
# ---------------------------------------------------------------------------
async def _fetch_duckduckgo_html(
    client: httpx.AsyncClient, query: str
) -> list[RawResult]:
    """Provedor 1 — endpoint HTML do DuckDuckGo (sem JavaScript)."""
    response = await client.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": settings.SCRAPER_REGION, "df": ""},
        headers=_browser_headers(referer="https://duckduckgo.com/"),
    )
    _raise_if_blocked("duckduckgo", response)
    soup = BeautifulSoup(response.text, "html.parser")

    results: list[RawResult] = []
    for position, block in enumerate(soup.select("div.result, div.web-result")):
        anchor = block.select_one("a.result__a")
        if not anchor or not anchor.get("href"):
            continue

        snippet_el = block.select_one(".result__snippet")
        results.append(
            RawResult(
                title=anchor.get_text(" ", strip=True),
                url=clean_ddg_redirect(str(anchor["href"])),
                snippet=snippet_el.get_text(" ", strip=True) if snippet_el else None,
                position=position,
            )
        )
    return results


async def _fetch_duckduckgo_lite(
    client: httpx.AsyncClient, query: str
) -> list[RawResult]:
    """Provedor 2 — versão Lite, layout tabular bem mais estável."""
    response = await client.post(
        "https://lite.duckduckgo.com/lite/",
        data={"q": query, "kl": settings.SCRAPER_REGION},
        headers=_browser_headers(referer="https://lite.duckduckgo.com/"),
    )
    _raise_if_blocked("duckduckgo-lite", response)
    soup = BeautifulSoup(response.text, "html.parser")

    results: list[RawResult] = []
    anchors = soup.select("a.result-link")
    for position, anchor in enumerate(anchors):
        href = anchor.get("href")
        if not href:
            continue

        # O snippet vive em uma <tr> seguinte, na célula .result-snippet.
        snippet = None
        row = anchor.find_parent("tr")
        for _ in range(3):
            row = row.find_next_sibling("tr") if row else None
            if row is None:
                break
            cell = row.select_one(".result-snippet")
            if cell:
                snippet = cell.get_text(" ", strip=True)
                break

        results.append(
            RawResult(
                title=anchor.get_text(" ", strip=True),
                url=clean_ddg_redirect(str(href)),
                snippet=snippet,
                position=position,
            )
        )
    return results


async def _fetch_bing(client: httpx.AsyncClient, query: str) -> list[RawResult]:
    """Provedor 3 — resultados orgânicos do Bing."""
    response = await client.get(
        "https://www.bing.com/search",
        params={"q": query, "setlang": "pt-br", "cc": "BR", "count": 15},
        headers=_browser_headers(referer="https://www.bing.com/"),
    )
    _raise_if_blocked("bing", response)
    soup = BeautifulSoup(response.text, "html.parser")

    results: list[RawResult] = []
    for position, item in enumerate(soup.select("li.b_algo")):
        anchor = item.select_one("h2 a")
        if not anchor or not anchor.get("href"):
            continue

        snippet_el = item.select_one(".b_caption p") or item.select_one("p")
        results.append(
            RawResult(
                title=anchor.get_text(" ", strip=True),
                url=clean_bing_redirect(str(anchor["href"])),
                snippet=snippet_el.get_text(" ", strip=True) if snippet_el else None,
                position=position,
            )
        )
    return results


async def _fetch_wikipedia(client: httpx.AsyncClient, query: str) -> list[RawResult]:
    """
    Provedor 4 — API pública da Wikipédia (JSON, sem scraping).

    Serve como rede de segurança: sempre devolve conteúdo enciclopédico
    pertinente, mesmo que todos os buscadores estejam indisponíveis.
    """
    response = await client.get(
        "https://pt.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 10,
            "format": "json",
            "utf8": 1,
        },
        headers=_wikipedia_headers(),
    )
    response.raise_for_status()
    payload = response.json()

    results: list[RawResult] = []
    for position, item in enumerate(payload.get("query", {}).get("search", [])):
        title = item.get("title", "")
        raw_snippet = item.get("snippet", "")
        # A API devolve o snippet com marcação <span class="searchmatch">.
        snippet = BeautifulSoup(raw_snippet, "html.parser").get_text(" ", strip=True)
        slug = title.replace(" ", "_")
        results.append(
            RawResult(
                title=title,
                url=f"https://pt.wikipedia.org/wiki/{slug}",
                snippet=snippet or None,
                position=position,
            )
        )
    return results


PROVIDERS: list[tuple[str, Any]] = [
    ("duckduckgo", _fetch_duckduckgo_html),
    ("duckduckgo-lite", _fetch_duckduckgo_lite),
    ("bing", _fetch_bing),
    ("wikipedia", _fetch_wikipedia),
]


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
def score_result(result: RawResult, query_terms: set[str]) -> float:
    """
    Calcula a pontuação de relevância (0–100) de um resultado.

    Componentes:
      * posição original no buscador  → até 20 pts
      * termos da consulta no título  → até 30 pts
      * termos da consulta no snippet → até 20 pts
      * confiabilidade do domínio     → -35 a +22 pts
      * qualidade do snippet          → até 8 pts
    """
    score = 0.0

    # 1) Confiança na posição entregue pelo buscador.
    score += max(0.0, 20.0 - result.position * 1.6)

    # 2) Aderência do título.
    title_terms = tokenize(result.title)
    if query_terms:
        overlap = len(query_terms & title_terms) / len(query_terms)
        score += overlap * 30.0

    # 3) Aderência do snippet.
    if result.snippet:
        snippet_terms = tokenize(result.snippet)
        if query_terms:
            overlap = len(query_terms & snippet_terms) / len(query_terms)
            score += overlap * 20.0
        # 4) Snippets muito curtos costumam indicar página pobre.
        score += min(8.0, len(result.snippet) / 25.0)

    # 5) Confiabilidade do domínio.
    domain = domain_of(result.url)
    for pattern, bonus in TRUSTED_PATTERNS.items():
        if re.search(pattern, domain):
            score += bonus
            break
    for pattern, penalty in PENALIZED_PATTERNS.items():
        if re.search(pattern, domain):
            score += penalty
            break

    # 6) Penaliza páginas de listagem/busca em vez de conteúdo.
    path = urlparse(result.url).path.lower()
    if any(seg in path for seg in ("/search", "/busca", "/tag/", "/categoria/")):
        score -= 12.0
    if path in ("", "/"):
        score -= 6.0  # home page raramente responde a um tópico específico

    return round(max(0.0, min(100.0, score)), 2)


def dedupe_and_rank(
    raw_results: Iterable[RawResult],
    query: str,
    limit: int,
    max_per_domain: int = 2,
) -> list[RawResult]:
    """Normaliza, remove duplicatas, pontua e devolve os `limit` melhores."""
    query_terms = tokenize(query)
    seen_urls: set[str] = set()
    candidates: list[RawResult] = []

    for result in raw_results:
        url = normalize_url(result.url)
        if not url or url in seen_urls:
            continue

        title = re.sub(r"\s+", " ", result.title).strip()
        if not title or len(title) < 3:
            continue

        seen_urls.add(url)

        snippet = result.snippet
        if snippet:
            snippet = re.sub(r"\s+", " ", snippet).strip()[:600]

        domain = domain_of(url)
        scored = RawResult(
            title=title[:300],
            url=url,
            snippet=snippet or None,
            position=result.position,
            source=domain,
        )
        scored.score = score_result(scored, query_terms)
        candidates.append(scored)

    # Ordena todos os candidatos por relevância decrescente (desempate por posição original).
    candidates.sort(key=lambda r: (-r.score, r.position))

    # Aplica o limite por domínio após a pontuação:
    # 1. Garante os melhores links de cada domínio (não os primeiros recebidos do buscador).
    # 2. Permite teto flexível (ex.: provedores mono-domínio como a Wikipédia podem entregar até `limit`).
    domain_count: dict[str, int] = {}
    selected: list[RawResult] = []
    for candidate in candidates:
        domain = candidate.source or domain_of(candidate.url)
        if domain_count.get(domain, 0) >= max_per_domain:
            continue
        domain_count[domain] = domain_count.get(domain, 0) + 1
        selected.append(candidate)
        if len(selected) >= limit:
            break

    return selected


# ---------------------------------------------------------------------------
# API pública do módulo
# ---------------------------------------------------------------------------
def build_query(raw_query: str, subject_hint: str | None = None) -> str:
    """
    Monta a consulta enviada ao buscador.

    A dica de matéria desambigua termos genéricos ("célula" em Biologia é
    diferente de "célula" em Química) sem poluir o texto digitado pelo usuário.
    """
    query = re.sub(r"\s+", " ", raw_query).strip()
    if subject_hint:
        hint = subject_hint.strip()
        if hint and strip_accents(hint.lower()) not in strip_accents(query.lower()):
            query = f"{query} {hint}"
    return query[:300]


async def search_content(
    raw_query: str,
    limit: int | None = None,
    subject_hint: str | None = None,
    use_cache: bool = True,
) -> SearchOutcome:
    """
    Busca conteúdo de apoio na web.

    Args:
        raw_query: Assunto a pesquisar (ex.: "partes do corpo humano").
        limit: Quantidade de links desejada (padrão: SCRAPER_MAX_RESULTS).
        subject_hint: Matéria associada, usada para refinar a consulta.
        use_cache: Se `False`, ignora o cache e força uma nova busca.

    Raises:
        SearchEngineError: se nenhum provedor responder.
    """
    limit = limit or settings.SCRAPER_MAX_RESULTS
    query = build_query(raw_query, subject_hint)
    cache_key = f"{query.lower()}::{limit}"
    started = time.perf_counter()

    if use_cache:
        cached: SearchOutcome | None = await _cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit para %r", query)
            return SearchOutcome(
                query=cached.query,
                provider=cached.provider,
                results=cached.results,
                cached=True,
                took_ms=int((time.perf_counter() - started) * 1000),
            )

    errors: list[str] = []

    async with _semaphore:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.SCRAPER_TIMEOUT),
            follow_redirects=True,
        ) as client:
            for provider_name, fetcher in PROVIDERS:
                if not _health.is_available(provider_name):
                    logger.debug("Provedor %s em cooldown, pulando", provider_name)
                    continue

                try:
                    raw_results = await fetcher(client, query)
                except Exception as exc:  # noqa: BLE001 — cascata de fallback
                    logger.warning("Provedor %s falhou: %s", provider_name, exc)
                    errors.append(f"{provider_name}: {exc}")
                    _health.record_failure(provider_name)
                    continue

                max_per_domain = limit if provider_name == "wikipedia" else 2
                ranked = dedupe_and_rank(
                    raw_results, query, limit, max_per_domain=max_per_domain
                )
                if ranked:
                    _health.record_success(provider_name)
                    outcome = SearchOutcome(
                        query=query,
                        provider=provider_name,
                        results=ranked,
                        cached=False,
                        took_ms=int((time.perf_counter() - started) * 1000),
                    )
                    await _cache.set(cache_key, outcome)
                    logger.info(
                        "Busca %r respondida por %s (%d resultados, %dms)",
                        query,
                        provider_name,
                        len(ranked),
                        outcome.took_ms,
                    )
                    return outcome

                # Sem resultados úteis não é bem uma exceção, mas conta como
                # falha pro disjuntor — é assim que um bloqueio "silencioso"
                # (ex.: DDG devolvendo uma página vazia com 200/202) se
                # manifesta.
                _health.record_failure(provider_name)
                logger.info("Provedor %s não retornou resultados úteis", provider_name)

    raise SearchEngineError(
        "Nenhum provedor de busca respondeu. Verifique sua conexão com a internet. "
        + (f"Detalhes: {'; '.join(errors[:3])}" if errors else "")
    )


async def clear_cache() -> None:
    """Esvazia o cache de buscas (usado em testes e na rota de diagnóstico)."""
    await _cache.clear()
