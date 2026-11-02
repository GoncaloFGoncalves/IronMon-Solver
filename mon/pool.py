"""O pool de defensores, pre-calculado uma vez por checkpoint.

A camada 0 corre 31 266 atacantes contra os mesmos 10 422 defensores. Tudo o
que depende so do defensor -- HP, defesas, Speed, efetividade por tipo -- faz-se
uma vez e reutiliza-se. Era 66% do tempo quando era refeito por atacante.

A aritmetica e a inteira do jogo, nao uma aproximacao: ha teste que confere
celula a celula contra o `variants.attack_damage`.
"""

import numpy as np

from mon.moves import PHYSICAL_TYPES
from mon.typechart import GEN_2_TO_5, TYPES_GEN_2_TO_5
from mon.variants import Variant

_TYPE_INDEX = {name: index for index, name in enumerate(TYPES_GEN_2_TO_5)}


class DefenderPool:
    """Os defensores em arrays, mais a matriz de efetividade por tipo."""

    def __init__(self, defenders: list[Variant]):
        self.defenders = defenders
        self.hp = np.array([d.hp for d in defenders], dtype=np.int64)
        self.defense = np.array([d.defense for d in defenders], dtype=np.int64)
        self.special_defense = np.array([d.special_defense for d in defenders],
                                        dtype=np.int64)
        self.speed = np.array([d.speed for d in defenders], dtype=np.int64)
        # Quem bate pelo lado mais forte. O dano que ele me faz esta no
        # `incoming.py`, com os moves reais: o golpe neutro de 80 que aqui
        # estava era cego aos tipos (CONTEXT.md 4b).
        self.physical = np.array([d.attack >= d.special_attack for d in defenders])
        self.attack = np.where(self.physical,
                               [d.attack for d in defenders],
                               [d.special_attack for d in defenders])
        self.effectiveness = np.array(
            [[GEN_2_TO_5.effectiveness(attacking, d.types) for d in defenders]
             for attacking in TYPES_GEN_2_TO_5], dtype=np.float64)
        # STAB do **defensor**, para quando e ele a bater (incoming.py). Uma
        # vez por checkpoint em vez de uma vez por move e por atacante: eram
        # 2 milhoes de iteracoes Python por celula.
        self.stab = np.array(
            [[1.5 if attacking in d.types else 1.0 for d in defenders]
             for attacking in TYPES_GEN_2_TO_5], dtype=np.float64)
        self.attack_both = np.array([d.attack for d in defenders], dtype=np.int64)
        self.special_attack = np.array([d.special_attack for d in defenders],
                                       dtype=np.int64)

    def damage_matrix(self, attacker: Variant, moves) -> np.ndarray:
        """`(move, defensor)` -> dano antes do roll, em inteiros do jogo."""
        factor = 2 * attacker.level // 5 + 2
        out = np.zeros((len(moves), len(self.defenders)), dtype=np.int64)
        for index, move in enumerate(moves):
            physical = move.type in PHYSICAL_TYPES
            attack = attacker.attack if physical else attacker.special_attack
            defense = self.defense if physical else self.special_defense
            damage = factor * move.power * attack // defense // 50 + 2
            if move.type in attacker.types:
                damage = damage * 3 // 2
            out[index] = (damage * self.effectiveness[_TYPE_INDEX[move.type]]
                          ).astype(np.int64)
        return out

