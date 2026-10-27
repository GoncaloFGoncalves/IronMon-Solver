"""Os dois motores respondem a mesma pergunta: tem de dar o mesmo numero.

O `battle.py` fecha a conta em forma analitica e e rapido; o `sequence.py`
anda turno a turno e devolve estados. Manter os dois so e indiferente se
concordarem -- e nao concordavam: havia 9 pp de diferenca, e era o
`battle.py` que estava errado (somava os rolls antes de aplicar o dano, em
vez de truncar golpe a golpe). Este teste e o que impede a reincidencia.
"""

import pytest

from mon.battle import Combatant, win_probability
from mon.sequence import Fighter, resolve

CASOS = [
    (36, 120, 42, 100), (70, 140, 45, 200), (25, 100, 25, 100),
    (90, 200, 70, 150), (40, 110, 55, 90), (50, 150, 45, 160),
    (33, 140, 38, 120), (53, 100, 53, 100),
]


@pytest.mark.parametrize("damage,hp,odamage,ohp", CASOS)
@pytest.mark.parametrize("speed,ospeed", [(40, 60), (60, 40)])
def test_both_engines_give_the_same_win_probability(
        damage, hp, odamage, ohp, speed, ospeed):
    analitico = win_probability(
        Combatant(damage=damage, hp=hp, speed=speed),
        Combatant(damage=odamage, hp=ohp, speed=ospeed),
        max_turns=30)
    turno_a_turno = resolve(
        Fighter(damage=damage, hp=hp, speed=speed),
        Fighter(damage=odamage, hp=ohp, speed=ospeed)).survival
    assert abs(analitico - turno_a_turno) < 1e-9
