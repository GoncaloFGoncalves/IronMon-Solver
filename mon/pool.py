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
        # O adversario bate pelo lado mais forte, com um golpe neutro de 80:
        # os moves dele sao randomizados e nao constam do mapa.
        self.physical = np.array([d.attack >= d.special_attack for d in defenders])
        self.attack = np.where(self.physical,
                               [d.attack for d in defenders],
                               [d.special_attack for d in defenders])
        self.effectiveness = np.array(
            [[GEN_2_TO_5.effectiveness(attacking, d.types) for d in defenders]
             for attacking in TYPES_GEN_2_TO_5], dtype=np.float64)

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

    def incoming_damage(self, attacker: Variant) -> np.ndarray:
        """O que cada defensor me faz por turno."""
        factor = 2 * self.defenders[0].level // 5 + 2
        defense = np.where(self.physical, attacker.defense,
                           attacker.special_defense)
        return factor * 80 * self.attack // defense // 50 + 2
