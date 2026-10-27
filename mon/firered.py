"""Dados de Gen 3 que o veekun nao tem certos: a disassembly do FireRed.

O `base_experience` do veekun e o valor **atual**: 375 das 386 especies
diferem, e os modernos rondam o dobro (Blissey 255 em Gen 3, 635 hoje). Usar
o veekun inflacionaria todo o EXP e com ele todos os niveis esperados. A
`pret/pokefirered` e a fonte autoritativa: e o proprio jogo.
"""

import re
import urllib.request
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/pret/pokefirered/master/src/data/pokemon/"
CACHE = Path(__file__).resolve().parent.parent / "data" / "pokefirered"

_BLOCK = re.compile(r"\[SPECIES_(\w+)\]\s*=\s*\{(.*?)\n    \},", re.S)
_YIELD = re.compile(r"\.expYield\s*=\s*(\d+)")
_CURVE = re.compile(r"\.growthRate\s*=\s*GROWTH_(\w+)")


def parse_species_info(text: str) -> dict[str, tuple[int, str]]:
    """Nome em minusculas -> (exp que da ao ser derrotado, curva)."""
    out = {}
    for name, body in _BLOCK.findall(text):
        exp_yield, curve = _YIELD.search(body), _CURVE.search(body)
        if exp_yield and curve:
            out[name.lower()] = (int(exp_yield.group(1)), curve.group(1))
    return out


def load_species_info() -> dict[str, tuple[int, str]]:
    return parse_species_info(_fetch("species_info.h"))


def _fetch(name: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / name
    if not local.exists():
        request = urllib.request.Request(BASE_URL + name,
                                         headers={"User-Agent": "mon"})
        local.write_text(urllib.request.urlopen(request).read().decode("utf-8"),
                         encoding="utf-8")
    return local.read_text(encoding="utf-8")
