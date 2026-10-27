"""Modelo de skew: perfis de stats derivados apenas do BST.

Em Kaizo IronMON os base stats sao redistribuidos ao acaso preservando o BST,
por isso o spread vanilla de uma especie nao existe na run. O que sobrevive e
o BST -- e daqui derivam-se os perfis plausiveis. Ver CONTEXT.md 3.2.

Os tres pares tem o mesmo estatuto e a mesma formula. Partindo de
(BST/6, BST/6), o skew e min/2 = BST/12, logo o stat favorecido fica em BST/4
e o outro no residual BST/12. Cada par soma sempre BST/3, por isso qualquer
perfil soma exatamente o BST.
"""

from dataclasses import dataclass
from itertools import product

HYBRID = "hybrid"
PHYSICAL, SPECIAL = "physical", "special"
DEF_TANK, SPDEF_TANK = "def_tank", "spdef_tank"
BULKY, FAST = "bulky", "fast"

# Por par: (variante que favorece o primeiro stat, variante que favorece o segundo)
_PAIRS = ((PHYSICAL, SPECIAL), (DEF_TANK, SPDEF_TANK), (FAST, BULKY))


@dataclass(frozen=True)
class StatProfile:
    hp: float
    attack: float
    defense: float
    special_attack: float
    special_defense: float
    speed: float
    offensive: str
    defensive: str
    tempo: str

    def is_all_hybrid(self) -> bool:
        return self.offensive == self.defensive == self.tempo == HYBRID

    def as_tuple(self) -> tuple:
        return (self.hp, self.attack, self.defense,
                self.special_attack, self.special_defense, self.speed)


def _split(bst: int, variant: str, favours_first: str) -> tuple[float, float]:
    """Reparte um par de stats, que vale sempre BST/3 no total."""
    if variant == HYBRID:
        return bst / 6, bst / 6
    concentrated, residual = bst / 4, bst / 12
    if variant == favours_first:
        return concentrated, residual
    return residual, concentrated


def _variants(pair: tuple[str, str]) -> tuple[str, str, str]:
    return (pair[0], pair[1], HYBRID)


def profiles(bst: int) -> list[StatProfile]:
    """Todos os perfis de stats plausiveis para um mon com este BST."""
    offensive_pair, defensive_pair, tempo_pair = _PAIRS
    out = []
    for offensive, defensive, tempo in product(
        _variants(offensive_pair), _variants(defensive_pair), _variants(tempo_pair)
    ):
        attack, special_attack = _split(bst, offensive, offensive_pair[0])
        defense, special_defense = _split(bst, defensive, defensive_pair[0])
        speed, hp = _split(bst, tempo, tempo_pair[0])
        out.append(StatProfile(hp, attack, defense, special_attack,
                               special_defense, speed,
                               offensive, defensive, tempo))
    return out
