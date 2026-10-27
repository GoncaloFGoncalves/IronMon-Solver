"""Carrega as tabelas do veekun/pokedex, com cache em disco.

A PokeAPI esta bloqueada neste ambiente e obrigaria a 386 chamadas; os CSVs do
veekun sao um ficheiro por tabela. Ver CONTEXT.md 2.0.

Camada fina de I/O: a logica de dominio vive em dex.py, que e puro.
"""

import csv
import urllib.request
from pathlib import Path

from mon.dex import GEN_3, Species, build_species
from mon.learnset import learn_schedule
from mon.moves import Move, build_moves
from mon.upside import Upside

BASE_URL = "https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "veekun"


def load_table(name: str) -> list[dict]:
    """Le uma tabela do veekun, descarregando-a na primeira vez."""
    path = CACHE_DIR / f"{name}.csv"
    if not path.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(BASE_URL + f"{name}.csv", timeout=60) as response:
            path.write_bytes(response.read())
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_species(numbers=GEN_3) -> list[Species]:
    """As especies do pool, prontas a usar pelo solver."""
    return build_species(
        pokemon=load_table("pokemon"),
        pokemon_types=load_table("pokemon_types"),
        pokemon_stats=load_table("pokemon_stats"),
        types=load_table("types"),
        numbers=numbers,
    )


GEN_3_MOVES = range(1, 355)


def load_changelog(ids=GEN_3_MOVES) -> dict[str, list]:
    """Historico de valores por move: (geracao em que mudou, valores de antes).

    Necessario porque o moves.csv guarda os valores atuais (ver moves.py).
    """
    names = {r["id"]: r["identifier"] for r in load_table("moves")
             if int(r["id"]) in ids}
    generation = {r["id"]: int(r["generation_id"])
                  for r in load_table("version_groups")}
    history: dict[str, list] = {}
    for row in load_table("move_changelog"):
        name = names.get(row["move_id"])
        if not name:
            continue
        changed = {field: row[field] for field in ("power", "pp", "accuracy")
                   if row.get(field)}
        if changed:
            history.setdefault(name, []).append(
                (generation[row["changed_in_version_group_id"]], changed))
    return history


def load_moves(ids=GEN_3_MOVES) -> list[Move]:
    """Os moves utilizaveis do pool, ja filtrados pelo GRUPOS.md."""
    return build_moves(
        moves=[r for r in load_table("moves") if int(r["id"]) in ids],
        types=load_table("types"),
        changelog=load_changelog(ids),
        drain=load_drain(ids),
        hits=load_hits(ids),
    )


def load_upside(ids=GEN_3_MOVES) -> dict[str, Upside]:
    """O efeito secundario de cada move, por nome.

    Os valores sao os atuais do veekun -- a armadilha de sempre. As chances de
    efeito nao estao no `move_changelog`, logo nao ha como as reverter para
    Gen 3 a partir daqui; ficam por verificar.
    """
    names = {r["id"]: r["identifier"] for r in load_table("moves")
             if int(r["id"]) in ids}
    ailments = {r["id"]: r["identifier"]
                for r in load_table("move_meta_ailments")}
    out = {}
    for row in load_table("move_meta"):
        if row["move_id"] not in names:
            continue
        name = names[row["move_id"]]
        ailment = ailments.get(row["meta_ailment_id"], "none")
        chance = int(row["ailment_chance"] or 0) / 100
        flinch = int(row["flinch_chance"] or 0) / 100
        # O tri-attack sorteia entre burn, freeze e paralysis; o veekun chama-lhe
        # "unknown". A paralisia representa-o: e a de maior swing das tres.
        if ailment == "unknown":
            ailment = "paralysis"
        if ailment == "none" or not chance:
            ailment, chance = "", 0.0
        if not chance and not flinch:
            continue
        out[name] = Upside(ailment=ailment, chance=chance, flinch=flinch)
    return out


def load_hits(ids=GEN_3_MOVES) -> dict[str, tuple[int, int]]:
    """Golpes por turno de cada move multi-golpe, por nome."""
    names = {r["id"]: r["identifier"] for r in load_table("moves")
             if int(r["id"]) in ids}
    out = {}
    for row in load_table("move_meta"):
        if row["move_id"] not in names:
            continue
        low, high = int(row["min_hits"] or 1), int(row["max_hits"] or 1)
        if (low, high) != (1, 1):
            out[names[row["move_id"]]] = (low, high)
    return out


def load_drain(ids=GEN_3_MOVES) -> dict[str, int]:
    """Quanto cada move cura, em % do dano causado. Negativos sao recuo."""
    names = {r["id"]: r["identifier"] for r in load_table("moves")
             if int(r["id"]) in ids}
    return {names[r["move_id"]]: int(r["drain"])
            for r in load_table("move_meta")
            if r["move_id"] in names and int(r["drain"] or 0) > 0}


FRLG = "firered-leafgreen"


def load_schedules(version=FRLG, numbers=GEN_3) -> dict[int, tuple[int, ...]]:
    """Os niveis a que cada especie aprende moves, por numero de dex."""
    version_id = next(r["id"] for r in load_table("version_groups")
                      if r["identifier"] == version)
    # Algumas especies guardam o learnset sob uma *forma* e nao sob o numero
    # base -- o Deoxys, porque cada jogo de Gen 3 tem uma forma diferente.
    # Mapear a forma de volta para a especie resolve-o sem casos especiais.
    species_of = {row["id"]: int(row["species_id"])
                  for row in load_table("pokemon")}
    by_form: dict[int, dict[int, list[int]]] = {}
    for row in load_table("pokemon_moves"):
        if (row["version_group_id"] != version_id
                or row["pokemon_move_method_id"] != "1"):
            continue
        number = species_of.get(row["pokemon_id"])
        if number not in numbers:
            continue
        form = int(row["pokemon_id"])
        by_form.setdefault(number, {}).setdefault(form, []).append(int(row["level"]))

    schedules = {}
    for number, forms in by_form.items():
        # A forma base quando existe; caso contrario a de id mais baixo.
        # Nunca fundir formas -- somaria os calendarios de ambas.
        chosen = forms.get(number) or forms[min(forms)]
        schedules[number] = learn_schedule(chosen)
    return schedules
