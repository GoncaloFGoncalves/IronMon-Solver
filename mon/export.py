"""Empacota a camada 0 para o visualizador.

Sao 281 394 celulas (9 checkpoints x 386 especies x 3 bandas x 27 perfis) e
35 MB de JSON. Numa pagina isso nao entra, mas os dois numeros de cada celula
cabem em `uint16` com 4 casas decimais, e a chave nao precisa de viajar:
deriva-se da posicao. Ficam 1.1 MB, que entram inline.

A ordem do indice e fixa e esta no proprio payload (`INDEX_ORDER`), para a
pagina a poder desfazer sem a adivinhar.
"""

import array
import base64
import json
from pathlib import Path

from mon.skew import profiles
from mon.trainers import SPLITS

SCALE = 10000
BANDS = ["sub-10", "sub-20", "20+"]
INDEX_ORDER = ("checkpoint", "species", "band", "profile")
SPECIES_COUNT = 386
PROFILES = [[p.offensive, p.defensive, p.tempo] for p in profiles(600)]
MISSING = 0xFFFF


def cell_index(checkpoint: int, species: int, band: int, profile: int) -> int:
    """Posicao de uma celula nos arrays planos."""
    return ((checkpoint * SPECIES_COUNT + species) * len(BANDS)
            + band) * len(PROFILES) + profile


def build_payload(root, checkpoints=SPLITS) -> dict:
    """Le as particoes do disco e devolve o payload do visualizador."""
    root = Path(root)
    total = len(checkpoints) * SPECIES_COUNT * len(BANDS) * len(PROFILES)
    win = array.array("H", [MISSING]) * total
    hp = array.array("H", [MISSING]) * total

    profile_index = {tuple(p): i for i, p in enumerate(PROFILES)}
    band_index = {name: i for i, name in enumerate(BANDS)}
    meta, known = [], []

    for ci, checkpoint in enumerate(checkpoints):
        folder = root / checkpoint
        per_species = [0] * SPECIES_COUNT
        level = opponent = 0
        for path in sorted(folder.glob("*.json")):
            block = json.loads(path.read_text())
            level, opponent = block["level"], block["opponent_level"]
            for row in block["rows"]:
                index = cell_index(ci, row["species"] - 1,
                                   band_index[row["band"]],
                                   profile_index[tuple(row["profile"])])
                win[index] = round(row["win"] * SCALE)
                hp[index] = round(row["hp_left"] * SCALE)
                per_species[row["species"] - 1] = row["known"]
        meta.append({"name": checkpoint, "level": level, "opponent": opponent})
        known.append(per_species)

    return {
        "order": list(INDEX_ORDER),
        "scale": SCALE,
        "missing": sum(1 for value in win if value == MISSING),
        "checkpoints": meta,
        "bands": BANDS,
        "profiles": PROFILES,
        "known": known,
        "win": base64.b64encode(win.tobytes()).decode(),
        "hp": base64.b64encode(hp.tobytes()).decode(),
    }


def engine_data() -> dict:
    """O que o motor do browser precisa para calcular um moveset concreto.

    Os stats derivam-se do BST pelo modelo de skew, logo nao viajam: so os
    moves, o chart de tipos e a divisao fisico/especial, que em Gen 3 e por
    tipo (`moves.PHYSICAL_TYPES`).
    """
    from mon.moves import PHYSICAL_TYPES
    from mon.typechart import GEN_2_TO_5_INTERACTIONS
    from mon.veekun import load_moves
    moves = [[m.name, m.type, m.power, m.pp] for m in load_moves()
             if m.kind == "power" and m.power]
    from mon.ivs import BANDS
    return {"moves": sorted(moves), "chart": GEN_2_TO_5_INTERACTIONS,
            "physical": sorted(PHYSICAL_TYPES),
            "ivs": {band: iv for band, iv in BANDS}}


def species_table() -> list:
    """`[numero, nome, tipos, bst]` por especie, na ordem do indice."""
    from mon.veekun import load_species
    return [[s.number, s.name, list(s.types), s.bst] for s in load_species()]
