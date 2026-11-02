"""O ranking por defensor -- o que a media da celula deita fora.

A camada 0 guarda `P(ganhar)` medio sobre 10 422 defensores. Um Gyarados com
def=212 e spd=86 da 0.96 nessa media **e perde 100% das vezes** contra uma
classe inteira de adversarios especiais. A media nao distingue um mon solido
de um mon com um buraco; esta tabela distingue.

Nao ha calculo novo: o vector por defensor ja existe dentro do `score.py` e
so se perde no `.mean()`. Custa ~26 ms recupera-lo.
"""

from dataclasses import dataclass

import numpy as np

from mon.orderstat import expected_best
from mon.pool import DefenderPool
from mon.variants import Variant
from mon.vector import defender_curves, ko_table, trade


@dataclass(frozen=True)
class Matchup:
    defender: Variant
    win: float
    hp_left: float        # fracao do meu maximo, dado que ganho
    damage_dealt: int     # o meu melhor golpe contra ele, antes do roll
    damage_taken: int     # o que ele me faz por turno


def _resolve(attacker: Variant, moves, pool: DefenderPool, known: int, table,
             threat_moves=None):
    """`(win, hp_left, damage, incoming)`, pelo mesmo nucleo que o kernel.

    Existe para que `worst_matchups` nao refaca o trabalho que o
    `per_defender` ja fez -- eram 366 ms em vez de 86.
    """
    from mon.score import blend
    wins, hps, damage, incoming, _ = blend(attacker, moves, pool, table,
                                           threat_moves)
    win, hp_left = expected_best(wins, min(known, len(moves)), companion=hps)
    return win, hp_left / attacker.hp, damage, incoming


def per_defender(attacker: Variant, moves, pool: DefenderPool,
                 known: int, table=None, threat_moves=None):
    """`(win, hp_left)` por defensor, antes de qualquer media.

    `known` e o numero de moves sorteados: com `known == len(moves)` a
    estatistica de ordem colapsa no maximo, que e o caso de um moveset
    concreto. `threat_moves` e o pool de onde saem os 4 moves **dele**, que
    nao e o meu (ver `score.score_variant`).
    """
    win, hp_left, _, _ = _resolve(attacker, moves, pool, known, table,
                                  threat_moves)
    return win, hp_left


def worst_matchups(attacker: Variant, moves, pool: DefenderPool,
                   known: int, limit: int = 20, table=None,
                   threat_moves=None) -> list[Matchup]:
    """Os `limit` defensores onde este atacante se sai pior, do pior para cima."""
    win, hp_left, damage, incoming = _resolve(attacker, moves, pool, known,
                                              table, threat_moves)
    # Desempate pelo HP que sobra: entre dois matchups que se perdem na mesma
    # medida, o pior e aquele que custa mais caro ganhar.
    order = np.lexsort((hp_left, win))[:max(0, min(limit, len(win)))]
    return [Matchup(defender=pool.defenders[index],
                    win=float(win[index]), hp_left=float(hp_left[index]),
                    damage_dealt=int(damage[:, index].max()),
                    damage_taken=int(incoming[index]))
            for index in order]
