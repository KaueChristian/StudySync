"""
Gera todos os arquivos do logo do StudySync a partir de uma única geometria.

    python brand/build.py

Saídas (todas versionadas — rode de novo só se a geometria ou as cores mudarem):
    brand/studysync-mark.svg        monograma sozinho, tinta sobre transparente
    brand/studysync-icon.svg        monograma no bloco verde-tinta (ícone do app)
    frontend/public/favicon.svg     = studysync-icon.svg
    frontend/public/favicon.ico     16, 32, 48
    frontend/public/icon-192.png    ícone das notificações do navegador
    desktop/StudySync.ico           ícone do .exe, da janela e do instalador

Só biblioteca padrão (sem Pillow/cairo): a forma é feita de retângulos e dois
arcos, então o rasterizador abaixo testa cada subpixel contra essa geometria.
O mesmo contorno está em `frontend/src/components/ui/Brand.jsx` — mudou
aqui, mude lá.
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Geometria — grade de 32 unidades, traço de 4.
# Com o ícone a 16 px, 1 unidade = 0,5 px: toda borda reta cai em pixel inteiro.
#
# O "S" tem o bojo de cima curvo (o ciclo de foco) e o de baixo reto (a célula
# da agenda). Terminais em x=24 e x=8 deixam as duas aberturas do S visíveis
# mesmo a 16 px.
# ---------------------------------------------------------------------------
TOP_END = 24  # onde termina o traço de cima
BOTTOM_END = 8  # onde termina o traço de baixo
ARC_CX, ARC_CY = 13, 11  # centro do bojo curvo
ARC_OUTER, ARC_INNER = 7, 3
TILE_RADIUS = 1.5  # cantos do bloco: 12 px a 256 px, quase reto a 16 px

MARK_PATH = (
    f"M{TOP_END} 4H13A7 7 0 0 0 13 18H22V24H{BOTTOM_END}V28H26V14H13"
    f"A3 3 0 0 1 13 8H{TOP_END}Z"
)

INK = (0x2B, 0x24, 0x20)  # --text do tema claro
BRAND = (0x3A, 0x63, 0x34)  # --color-brand-600
PAPER = (0xFF, 0xFD, 0xF8)  # --color-paper


def in_mark(x: float, y: float) -> bool:
    """Mesmo contorno de MARK_PATH, como união de peças."""
    if 4 <= y <= 8 and 13 <= x <= TOP_END:  # traço de cima
        return True
    if x <= 13:  # bojo curvo (meio anel à esquerda)
        d = math.hypot(x - ARC_CX, y - ARC_CY)
        if ARC_INNER <= d <= ARC_OUTER:
            return True
    if 14 <= y <= 18 and 13 <= x <= 26:  # traço do meio
        return True
    if 22 <= x <= 26 and 14 <= y <= 28:  # haste da direita
        return True
    return 24 <= y <= 28 and BOTTOM_END <= x <= 26  # traço de baixo


def in_tile(x: float, y: float) -> bool:
    r = TILE_RADIUS
    cx = min(max(x, r), 32 - r)
    cy = min(max(y, r), 32 - r)
    return 0 <= x <= 32 and 0 <= y <= 32 and math.hypot(x - cx, y - cy) <= r


def render_icon(size: int) -> list[tuple[int, int, int, int]]:
    """Bloco verde com o S em papel, RGBA sem pré-multiplicar, linha a linha."""
    n = 8 if size <= 64 else 4  # subamostras por eixo
    scale = 32 / size
    pixels = []
    for py in range(size):
        for px in range(size):
            tile = mark = 0
            for sy in range(n):
                y = (py + (sy + 0.5) / n) * scale
                for sx in range(n):
                    x = (px + (sx + 0.5) / n) * scale
                    if in_tile(x, y):
                        tile += 1
                        mark += in_mark(x, y)
            if tile == 0:
                pixels.append((0, 0, 0, 0))
                continue
            t = mark / tile
            r, g, b = (round(c0 + (c1 - c0) * t) for c0, c1 in zip(BRAND, PAPER))
            pixels.append((r, g, b, round(255 * tile / (n * n))))
    return pixels


# ---------------------------------------------------------------------------
# Codificadores
# ---------------------------------------------------------------------------
def encode_png(size: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    raw = bytearray()
    for row in range(size):
        raw.append(0)  # filtro "None"
        for r, g, b, a in pixels[row * size : (row + 1) * size]:
            raw += bytes((r, g, b, a))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def encode_dib(size: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    """Entrada BMP de .ico (32 bpp + máscara AND) — a forma mais compatível."""
    xor = bytearray()
    mask_row = ((size + 31) // 32) * 4
    mask = bytearray()
    for row in reversed(range(size)):  # DIB é de baixo para cima
        line = pixels[row * size : (row + 1) * size]
        for r, g, b, a in line:
            xor += bytes((b, g, r, a))
        bits = bytearray(mask_row)
        for i, (*_, a) in enumerate(line):
            if a == 0:
                bits[i // 8] |= 0x80 >> (i % 8)
        mask += bits
    header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, len(xor) + len(mask), 0, 0, 0, 0)
    return header + bytes(xor) + bytes(mask)


def encode_ico(sizes: list[int]) -> bytes:
    # PNG só nos tamanhos grandes (onde BMP pesaria); BMP nos pequenos, que
    # qualquer leitor de .ico entende.
    images = []
    for size in sizes:
        pixels = render_icon(size)
        images.append(encode_png(size, pixels) if size >= 128 else encode_dib(size, pixels))

    out = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    for size, data in zip(sizes, images):
        dim = 0 if size >= 256 else size
        out += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(images)


def hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def main() -> None:
    icon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        f'<rect width="32" height="32" rx="{TILE_RADIUS}" fill="{hex_color(BRAND)}"/>'
        f'<path d="{MARK_PATH}" fill="{hex_color(PAPER)}"/></svg>\n'
    )
    mark_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        f'<path d="{MARK_PATH}" fill="{hex_color(INK)}"/></svg>\n'
    )
    outputs: dict[Path, bytes] = {
        ROOT / "brand" / "studysync-mark.svg": mark_svg.encode(),
        ROOT / "brand" / "studysync-icon.svg": icon_svg.encode(),
        ROOT / "frontend" / "public" / "favicon.svg": icon_svg.encode(),
        ROOT / "frontend" / "public" / "favicon.ico": encode_ico([16, 32, 48]),
        ROOT / "frontend" / "public" / "icon-192.png": encode_png(192, render_icon(192)),
        ROOT / "desktop" / "StudySync.ico": encode_ico([16, 20, 24, 32, 40, 48, 64, 128, 256]),
    }
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"{path.relative_to(ROOT)}  ({len(data):,} bytes)")


if __name__ == "__main__":
    main()
