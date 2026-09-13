"""
Sanitização de entrada — defesa contra XSS armazenado.

O conteúdo das anotações é Markdown. Como Markdown aceita HTML inline, um
usuário poderia salvar `<script>` ou `<img onerror=...>` e o payload seria
executado no navegador de quem visualizasse a nota.

Estratégia de defesa em profundidade:
1. **Backend (aqui):** `bleach` remove tags/atributos perigosos na escrita.
2. **Frontend:** `react-markdown` não interpreta HTML bruto por padrão.
"""

from __future__ import annotations

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


def sanitize_html(value: str | None) -> str | None:
    """Remove tags e atributos perigosos, preservando a formatação legítima."""
    if value is None:
        return None
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_text(value: str | None) -> str | None:
    """
    Sanitização estrita: descarta *qualquer* marcação HTML.

    Usada em campos de texto simples (títulos, nomes de matérias, tags),
    onde HTML nunca é legítimo.
    """
    if value is None:
        return None
    cleaned = bleach.clean(value, tags=set(), attributes={}, strip=True)
    return cleaned.strip()


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
