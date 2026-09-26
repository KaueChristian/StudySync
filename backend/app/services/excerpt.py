"""
Resumo em texto puro de uma anotação em Markdown (cards da listagem e do
painel).

Remove a *sintaxe* do Markdown e mantém o *conteúdo*: o texto de um link
fica e a URL sai; o código inline fica sem as crases; pontuação comum
("bem-vindo", "(de novo)!") não é tocada.
"""

from __future__ import annotations

import re

_FENCED_CODE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[^\n]*$", re.DOTALL | re.MULTILINE)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_INLINE_CODE = re.compile(r"`+([^`]*)`+")
_TABLE_RULE = re.compile(r"^[ \t]*\|?[ \t:|-]+\|[ \t:|-]*$", re.MULTILINE)
_HORIZONTAL_RULE = re.compile(r"^[ \t]*([-*_])([ \t]*\1){2,}[ \t]*$", re.MULTILINE)
_LINE_MARKERS = re.compile(
    r"^[ \t]*(?:>[ \t]?)*[ \t]*(?:#{1,6}[ \t]+|[-*+][ \t]+(?:\[[ xX]\][ \t]+)?|\d+[.)][ \t]+)?",
    re.MULTILINE,
)
# Marcador de ênfase encosta numa palavra de um lado só: `*abre` e `fecha*`.
# "2 * 3" (espaço dos dois lados) e "snake_case" (palavra dos dois) ficam.
_EMPHASIS = re.compile(r"\*\*|~~|(?<!\w)[*_]+(?=\w)|(?<=\w)[*_]+(?!\w)")


def markdown_excerpt(content: str | None, length: int = 180) -> str:
    """Texto puro dos primeiros `length` caracteres, com reticências se cortado."""
    text = content or ""
    text = _FENCED_CODE.sub(" ", text)
    text = _IMAGE.sub(r"\1", text)
    text = _LINK.sub(r"\1", text)
    text = _TABLE_RULE.sub(" ", text)
    text = _HORIZONTAL_RULE.sub(" ", text)
    text = _LINE_MARKERS.sub("", text)
    # Crases antes da ênfase: o que está dentro do código é literal.
    parts = _INLINE_CODE.split(text)
    text = "".join(
        part if index % 2 else _EMPHASIS.sub("", part).replace("|", " ")
        for index, part in enumerate(parts)
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length] + ("…" if len(text) > length else "")
