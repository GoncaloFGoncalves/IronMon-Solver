"""Motor de troca: quem ganha o combate, nao quanto dano leva.

A metrica do solver e o desfecho, nao a percentagem de dano (CONTEXT.md 3.6).
E preciso assim porque a paralisia e o flinch nao alteram o dano de golpe
nenhum -- so se veem na contagem de turnos e na ordem de ataque.
"""

from dataclasses import dataclass
from math import comb

from mon.damage import probability_of_ko


def moves_first(speed: float, opposing_speed: float) -> float:
    """Probabilidade de atacar primeiro. Empate resolve-se a sorte."""
    if speed == opposing_speed:
        return 0.5
    return 1.0 if speed > opposing_speed else 0.0


@dataclass(frozen=True)
class Combatant:
    damage: float          # dano antes do roll, por turno
    hp: float
    speed: float
    action_chance: float = 1.0   # probabilidade de agir num turno dado
    residual: float = 0.0        # HP perdido por turno a status


def win_probability(me: Combatant, them: Combatant, max_turns: int = 4) -> float:
    """Probabilidade de eu derrubar o adversario antes de ele me derrubar.

    Somada turno a turno: em cada turno n, ganho se o derrubo exatamente
    nesse turno e ele ainda nao me derrubou. Quem ataca primeiro decide
    quantos golpes ele ja teve quando eu dou o meu.
    """
    first = moves_first(me.speed, them.speed)
    total = 0.0
    for turn in range(1, max_turns + 1):
        ko_now = (_ko_by_turn(me, them, turn)
                  - _ko_by_turn(me, them, turn - 1))
        if ko_now <= 0:
            continue
        # Se ataco primeiro ele ja teve turn-1 turnos quando eu dou o meu;
        # se ataco depois, ja teve turn.
        survives_first = 1 - _ko_by_turn(them, me, turn - 1)
        survives_second = 1 - _ko_by_turn(them, me, turn)
        total += ko_now * (first * survives_first + (1 - first) * survives_second)
    return total


def _ko_by_turn(attacker: Combatant, defender: Combatant, turns: int) -> float:
    """Probabilidade de o atacante ja ter derrubado o defensor ao fim de N turnos.

    Turnos decorridos nao sao golpes acertados: com `action_chance` abaixo de 1
    o atacante perde turnos (paralisia, flinch, freeze). Somamos sobre quantos
    golpes chegou a dar, ponderado pela binomial.
    """
    if turns <= 0:
        return 0.0
    # O residual atua no fim de cada turno, logo ao turno N ja levou N-1.
    remaining = defender.hp - (turns - 1) * defender.residual
    if remaining <= 0:
        return 1.0
    acts = attacker.action_chance
    if acts >= 1.0:
        return probability_of_ko(attacker.damage, remaining, turns)
    return sum(
        comb(turns, hits) * acts**hits * (1 - acts)**(turns - hits)
        * probability_of_ko(attacker.damage, remaining, hits)
        for hits in range(turns + 1)
    )
