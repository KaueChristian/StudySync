"""
Sanitização: remove HTML perigoso sem corromper o texto do usuário.

Regressão de 2026-09-25: o `bleach` escapava o texto (`P&D` → `P&amp;D`,
`> citação` → `&gt; citação`), corrompendo títulos, tags e o Markdown.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import pytest

from app.core.sanitize import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_TAGS,
    normalize_tag,
    sanitize_html,
    sanitize_text,
)

TAG_LIKE = re.compile(r"<[A-Za-z/!?][^>]*>")

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    '<a href="javascript:alert(1)">x</a>',
    "<a href='data:text/html,<script>alert(1)</script>'>x</a>",
    "<<b>script>alert(1)<</b>/script>",
    "<<x>script>alert(1)<</x>/script>",
    "<scr<script>ipt>alert(1)</script>",
    "<iframe src=//evil></iframe>",
    "<IMG SRC=JaVaScRiPt:alert(1)>",
    "<img src=x\nonerror=alert(1)>",
    '<a href="jav&#x09;ascript:alert(1)">x</a>',
    "<style>body{}</style>",
    "<!--<script>alert(1)</script>-->",
    "<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>",
    "<p onclick=alert(1)>t</p>",
    '<a href="https://ok.com" onclick="x">ok</a>',
    "<details open ontoggle=alert(1)>",
    "<object data=x>",
    "<svg><script>alert(1)</script></svg>",
    "<form action=javascript:alert(1)><button>x</button></form>",
]


class _DangerFinder(HTMLParser):
    """Coleta tudo que um navegador executaria ou carregaria de forma insegura."""

    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            self.found.append(tag)
        for name, value in attrs:
            if name.startswith("on") or name not in ALLOWED_ATTRIBUTES.get(tag, []):
                self.found.append(f"{tag}[{name}]")
            if value and re.match(r"\s*(javascript|data|vbscript):", value, re.I):
                self.found.append(f"{tag}[{name}={value}]")


def _dangers(html: str) -> list[str]:
    finder = _DangerFinder()
    finder.feed(html)
    finder.close()
    return finder.found


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_markdown_sanitizer_neutralizes_xss(payload):
    assert _dangers(sanitize_html(payload)) == []


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_text_sanitizer_leaves_no_markup(payload):
    assert not TAG_LIKE.search(sanitize_text(payload))


@pytest.mark.parametrize(
    "value",
    [
        "P&D",
        "Física & Química",
        "x < 5 e y > 3",
        "x<y",
        "a <= b >= c",
        "C & C++",
        "Tom &amp; Jerry",  # entidade digitada pelo usuário continua literal
        "setas -> e <-",
        'aspas "duplas" e \'simples\'',
    ],
)
def test_plain_text_is_kept_verbatim(value):
    assert sanitize_text(value) == value
    assert sanitize_text(sanitize_text(value)) == value


def test_plain_text_drops_tags_but_keeps_their_text():
    assert sanitize_text("<b>Bio</b>logia") == "Biologia"
    assert sanitize_text("  <i>espaço</i>  ") == "espaço"
    assert sanitize_text(None) is None


def test_markdown_is_kept_verbatim():
    markdown = (
        "> citação importante\n\n"
        "Se `a < b && c` então -> resultado <= 3 & >= 1\n\n"
        "```python\nif x < 3 and y > 2: pass\n```\n\n"
        '**negrito** <b>ok</b> <a href="https://x.com">link</a>\n\n'
        "| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        "- [x] tarefa\n- [ ] outra"
    )
    assert sanitize_html(markdown) == markdown
    assert sanitize_html(None) is None


def test_markdown_drops_only_the_dangerous_parts():
    cleaned = sanitize_html('Antes <img src=x onerror=alert(1)> depois & fim')
    assert cleaned == 'Antes <img src="x"> depois & fim'


def test_tags_keep_symbols():
    assert normalize_tag("  C&C  ") == "c&c"
    assert normalize_tag("<b>Prova</b>  Final") == "prova final"
