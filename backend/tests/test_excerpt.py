"""Resumo em texto puro das anotações (listagem e painel)."""

from __future__ import annotations

import pytest

from app.services.excerpt import markdown_excerpt


@pytest.mark.parametrize(
    "markdown, expected",
    [
        # Regressão: código inline e pontuação comum sumiam do resumo.
        ("Se `a < b && c > d` então -> ok", "Se a < b && c > d então -> ok"),
        ("Bem-vindo (de novo)! Tudo certo?", "Bem-vindo (de novo)! Tudo certo?"),
        ("snake_case e 2 * 3", "snake_case e 2 * 3"),
        # Sintaxe de Markdown sai, o conteúdo fica.
        ("# Título\n\n> citação\n\n- item um\n1. item dois", "Título citação item um item dois"),
        ("**negrito**, _itálico_ e ~~riscado~~", "negrito, itálico e riscado"),
        ("Veja [a Khan Academy](https://khan.org) e ![diagrama](x.png)", "Veja a Khan Academy e diagrama"),
        ("- [x] feito\n- [ ] pendente", "feito pendente"),
        ("```python\nprint(1)\n```\nDepois do código", "Depois do código"),
        ("| a | b |\n|---|---|\n| 1 | 2 |", "a b 1 2"),
        ("Antes\n\n---\n\nDepois", "Antes Depois"),
    ],
)
def test_excerpt_keeps_the_text(markdown, expected):
    assert markdown_excerpt(markdown) == expected


def test_excerpt_truncates_with_ellipsis():
    assert markdown_excerpt("palavra " * 50, length=20) == "palavra palavra pala…"
    assert markdown_excerpt("") == ""
    assert markdown_excerpt(None) == ""
