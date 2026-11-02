"""O kernel: o score de uma variante contra o pool de defensores.

Uma celula guarda dois numeros (CONTEXT.md 3.6b): `P(ganhar)` e
`E[HP restante | ganhar]`. O primeiro diz se o matchup se ganha, o segundo e
a moeda da sobrevivencia numa dungeon onde nao ha cura.

O moveset **nao se escolhe**: no Kaizo calha. Pontua-se cada move do pool
contra cada defensor e combina-se o melhor dos N que o mon conhece por
estatistica de ordem (`orderstat.py`) -- sem amostragem e sem ruido. A
selecao gulosa respondia a "qual o melhor moveset possivel", que e uma
pergunta que o jogo nunca faz.

A habilidade entra **por cima** do moveset, nunca antes (3.5b).
"""

from dataclasses import dataclass

import numpy as np

from mon.abilities import MonContext, utilization
from mon.battle import Combatant
from mon.incoming import incoming_profile, lethal_cap
from mon.orderstat import expected_best
from mon.pool import DefenderPool
from mon.upside import Upside
from mon.upside import value as upside_value
from mon.variants import Variant
from mon.vector import defender_curves, ko_table, trade

SLOTS = 4


@dataclass(frozen=True)
class Cell:
    win: float          # P(ganhar), media sobre o pool
    hp_left: float      # E[HP restante | ganhar], em fracao do meu maximo
    known: int          # quantos moves o mon conhecia
    risk: float = 0.0   # P(ele ter sorteado um move que me mata de um)


def score_variant(attacker: Variant, moves, pool: DefenderPool,
                  known: int = SLOTS, ability: str = "",
                  upsides=None, table=None, threat_moves=None) -> Cell:
    """A celula: esta variante, com N moves aleatorios deste pool de moves.

    `threat_moves` e o pool de onde saem os **4 moves do adversario**, que e
    sempre o do jogo e nao o meu: o que eu sei nao muda o que ele pode ter.
    Na camada 0 os dois coincidem, mas numa consulta de moveset concreto eu
    passo 4 moves e ele continua a sortear dos 194 -- daqui o parametro.
    """
    threat_moves = moves if threat_moves is None else threat_moves
    table = ko_table() if table is None else table
    if not moves or not pool.defenders:
        return Cell(0.0, 0.0, 0)

    # 4b: depois de cortar o overkill so ha dois cenarios distinguiveis -- ele
    # tirou um move que me mata de um, ou nao tirou. Um escalar unico entre os
    # dois seria lido pelo motor como "tres golpes para me matar", e nunca sao.
    wins, hps, damage, safe, share = blend(attacker, moves, pool, table,
                                           threat_moves)
    if upsides:
        wins = _with_upside(wins, attacker, moves, pool, safe, upsides)

    known = min(known, len(moves))
    win, hp_left = expected_best(wins, known, companion=hps)
    cell = Cell(float(win.mean()), float(hp_left.mean()) / attacker.hp, known,
                float(share.mean()))
    return _with_ability(cell, attacker, moves, pool, safe, damage, ability)


def blend(attacker: Variant, moves, pool: DefenderPool, table=None,
          threat_moves=None):
    """`(wins, hps, damage, safe, share)` -- os tres primeiros em
    (move, defensor), ja pesados pelos dois cenarios de 4b.

    E o nucleo partilhado pelo kernel e pelo `matchups.py`: dois caminhos a
    calcular a mesma coisa de maneiras diferentes ja custaram dois bugs a
    este projeto (CONTEXT.md 4).
    """
    table = ko_table() if table is None else table
    threat_moves = moves if threat_moves is None else threat_moves
    share, safe = incoming_profile(attacker, threat_moves, pool)
    letal = np.full(len(pool.hp), float(lethal_cap(attacker.hp)))
    first = np.where(attacker.speed > pool.speed, 1.0,
                     np.where(attacker.speed < pool.speed, 0.0, 0.5))
    damage = pool.damage_matrix(attacker, moves)

    wins = np.zeros(damage.shape, dtype=np.float64)
    hps = np.zeros(damage.shape, dtype=np.float64)
    for incoming, weight in ((letal, share), (safe, 1.0 - share)):
        curves = defender_curves(attacker.hp, incoming, table)
        for index in range(len(moves)):
            won, left = trade(damage[index], attacker.hp, incoming,
                              pool.hp, first, table, curves=curves)
            wins[index] += weight * won
            hps[index] += weight * left
    return wins, hps, damage, safe, share


def _scenario_cells(attacker: Variant, moves, pool: DefenderPool,
                    known: int = SLOTS, table=None, threat_moves=None):
    """As duas celulas extremas, para inspeccao: so letal e so seguro.

    A celula real fica entre elas, pesada pela quota letal. Existe para o
    teste poder prender o invariante, e para uma consulta poder mostrar
    "morres de um golpe em X% dos sorteios" em vez de so a media.
    """
    table = ko_table() if table is None else table
    share, safe = incoming_profile(attacker, moves if threat_moves is None
                                   else threat_moves, pool)
    letal = np.full(len(pool.hp), float(lethal_cap(attacker.hp)))
    first = np.where(attacker.speed > pool.speed, 1.0,
                     np.where(attacker.speed < pool.speed, 0.0, 0.5))
    damage = pool.damage_matrix(attacker, moves)
    known = min(known, len(moves))

    out = []
    for incoming in (letal, safe):
        curves = defender_curves(attacker.hp, incoming, table)
        wins = np.empty(damage.shape, dtype=np.float64)
        hps = np.empty(damage.shape, dtype=np.float64)
        for index in range(len(moves)):
            wins[index], hps[index] = trade(damage[index], attacker.hp,
                                            incoming, pool.hp, first, table,
                                            curves=curves)
        win, hp_left = expected_best(wins, known, companion=hps)
        out.append(Cell(float(win.mean()),
                        float(hp_left.mean()) / attacker.hp, known))
    return tuple(out)


def _median(values) -> int:
    return int(np.argsort(values)[len(values) // 2])


def _with_upside(wins, attacker, moves, pool, incoming, upsides):
    """O efeito secundario entra no score do **proprio move**, nao a parte.

    O swing depende do atacante e do defensor (GRUPOS.md C), mas medi-lo por
    defensor custava mais que a celula. Mede-se contra o defensor mediano; o
    swing exato por defensor sai numa consulta.
    """
    middle = _median(incoming)
    me = Combatant(damage=1.0, hp=attacker.hp, speed=attacker.speed)
    them = Combatant(damage=float(incoming[middle]), hp=float(pool.hp[middle]),
                     speed=float(pool.speed[middle]))
    out = wins.copy()
    for index, move in enumerate(moves):
        upside = upsides.get(move.name)
        if upside is None:
            continue
        swing = (upside_value(me, them, upside, move.is_physical)
                 - upside_value(me, them, Upside(), move.is_physical))
        out[index] = np.clip(out[index] + swing, 0.0, 1.0)
    return out


def _with_ability(cell: Cell, attacker: Variant, moves, pool: DefenderPool,
                  incoming, damage, ability: str) -> Cell:
    """Swing medido contra o defensor mediano do pool.

    Fazer 10 422 chamadas escalares por celula custava mais que a celula
    toda; o swing exato por defensor sai do `abilities.py` numa consulta.
    """
    if not ability:
        return cell
    middle = _median(incoming)
    me = Combatant(damage=float(damage.max()), hp=attacker.hp,
                   speed=attacker.speed)
    them = Combatant(damage=float(incoming[middle]), hp=float(pool.hp[middle]),
                     speed=float(pool.speed[middle]))
    swing = utilization(ability, MonContext(
        me=me, them=them,
        physical=any(move.is_physical for move in moves),
        incoming_physical=bool(pool.physical[middle])))
    return Cell(max(0.0, min(1.0, cell.win + swing)), cell.hp_left,
                cell.known, cell.risk)
