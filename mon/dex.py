"""Pokedex: especies e o que sobrevive a randomizacao do Kaizo.

De uma especie so sobrevivem os tipos e o BST (CONTEXT.md 1.1) -- e sao esses
os dois campos que interessam ao solver. O nome e o numero servem so de indice.
"""

from dataclasses import dataclass
from typing import Container

# O pool do solver: os 386 mons de Gen 3 (Kanto + Hoenn).
GEN_3 = range(1, 387)


@dataclass(frozen=True)
class Species:
    number: int
    name: str
    types: tuple[str, ...]
    bst: int


def build_species(pokemon, pokemon_types, pokemon_stats, types,
                  numbers: Container[int] | None = None) -> list[Species]:
    """Cruza as tabelas do veekun/pokedex numa lista de especies."""
    type_name = {row["id"]: row["identifier"].upper() for row in types}

    types_of: dict[str, list[tuple[int, str]]] = {}
    for row in pokemon_types:
        types_of.setdefault(row["pokemon_id"], []).append(
            (int(row["slot"]), type_name[row["type_id"]])
        )

    bst_of: dict[str, int] = {}
    for row in pokemon_stats:
        bst_of[row["pokemon_id"]] = bst_of.get(row["pokemon_id"], 0) + int(row["base_stat"])

    wanted = [row for row in pokemon
              if numbers is None or int(row["id"]) in numbers]
    return [
        Species(
            number=int(row["id"]),
            name=row["identifier"],
            types=tuple(name for _, name in sorted(types_of[row["id"]])),
            bst=bst_of[row["id"]],
        )
        for row in wanted
    ]
