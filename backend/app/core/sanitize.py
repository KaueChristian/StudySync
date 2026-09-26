"""
Sanitização de entrada — defesa contra XSS armazenado.

O conteúdo das anotações é Markdown. Como Markdown aceita HTML inline, um
usuário poderia salvar `<script>` ou `<img onerror=...>` e o payload seria
executado no navegador de quem visualizasse a nota.

Estratégia de defesa em profundidade:
1. **Backend (aqui):** `bleach` remove tags/atributos perigosos na escrita.
2. **Frontend:** `react-markdown` não interpreta HTML bruto por padrão.

O que é gravado continua sendo o texto do usuário, não HTML: só as tags saem.
O `bleach` sozinho também escaparia o texto (`P&D` → `P&amp;D`, `> citação`
→ `&gt; citação`), o que corrompia títulos, tags e o Markdown das anotações.
"""

from __future__ import annotations

import re
import secrets

import bleach

# Tags HTML consideradas seguras dentro do Markdown das anotações.
ALLOWED_TAGS: set[str] = {
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "del",
    "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "li",
    "ol", "p", "pre", "span", "strong", "sub", "sup", "table", "tbody",
    "td", "th", "thead", "tr", "ul",
}

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["class"],
    "code": ["class"],
    "th": ["align"],
    "td": ["align"],
}

# Protocolos permitidos em href/src — bloqueia `javascript:` e `data:`.
ALLOWED_PROTOCOLS: set[str] = {"http", "https", "mailto"}


# O que um navegador trata como tag: `<` seguido de letra, `/`, `!` ou `?`,
# até o próximo `>`. Um `<` solto ("x < 5", "<3", "<-") é só texto.
_TAG_LIKE = re.compile(r"<[A-Za-z/!?][^>]*>")

# Remover um pedaço pode juntar outro numa tag nova (`<<b>script>`); por isso
# as funções repetem até o resultado parar de mudar.
_MAX_PASSES = 10


def _clean_markup_once(value: str) -> str:
    """
    Passa só as tags pelo `bleach` e devolve o texto entre elas intacto.

    O texto vira marcadores (sem `&`, `<` ou `>`, então o `bleach` não os
    escapa), o documento inteiro é limpo de uma vez — assim o `bleach` enxerga
    a estrutura real das tags — e os marcadores voltam a ser o texto original.
    """
    nonce = secrets.token_hex(4)
    texts: list[str] = []

    def placeholder(text: str) -> str:
        texts.append(text)
        return f"{nonce}{len(texts) - 1}"

    parts: list[str] = []
    position = 0
    for match in _TAG_LIKE.finditer(value):
        if match.start() > position:
            parts.append(placeholder(value[position : match.start()]))
        parts.append(match.group(0))
        position = match.end()
    if position < len(value):
        parts.append(placeholder(value[position:]))

    cleaned = bleach.clean(
        "".join(parts),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return re.sub(
        rf"{nonce}(\d+)", lambda m: texts[int(m.group(1))], cleaned
    )


def sanitize_html(value: str | None) -> str | None:
    """Remove tags e atributos perigosos do Markdown, preservando o resto."""
    if value is None:
        return None
    for _ in range(_MAX_PASSES):
        cleaned = _clean_markup_once(value)
        if cleaned == value:
            return cleaned
        value = cleaned
    # Não estabilizou: entrada construída para enganar o limpador. Cai no
    # `bleach` puro, que escapa tudo — feio, mas seguro.
    return bleach.clean(
        value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS, strip=True,
    )


def sanitize_text(value: str | None) -> str | None:
    """
    Sanitização estrita: descarta *qualquer* marcação HTML.

    Usada em campos de texto simples (títulos, nomes de matérias, tags),
    onde HTML nunca é legítimo. O resto do texto fica como foi digitado — a
    interface exibe esses campos como texto, nunca como HTML.
    """
    if value is None:
        return None
    for _ in range(_MAX_PASSES):
        cleaned = _TAG_LIKE.sub("", value)
        if cleaned == value:
            break
        value = cleaned
    else:
        value = _TAG_LIKE.sub("", value).replace("<", "")
    return value.strip()


def normalize_tag(value: str) -> str:
    """Normaliza uma tag: sem HTML, minúscula, espaços colapsados."""
    cleaned = sanitize_text(value) or ""
    return " ".join(cleaned.lower().split())


def strip_accents(value: str | None) -> str:
    """Remove acentuação e converte para minúsculas para buscas e ordenação insensíveis."""
    if not value:
        return ""
    import unicodedata

    return "".join(
        c for c in unicodedata.normalize("NFD", str(value))
        if unicodedata.category(c) != "Mn"
    ).lower()


def escape_like(value: str) -> str:
    """Escapa curingas da cláusula LIKE (%, _ e \\)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
