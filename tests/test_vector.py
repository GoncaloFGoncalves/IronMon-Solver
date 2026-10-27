import numpy as np
import pytest

from mon.battle import Combatant, win_probability
from mon.damage import HITS_TWO_TO_FIVE, probability_of_ko, probability_of_ko_multi
from mon.vector import (MAX_DAMAGE, MAX_HP, ko_table, win_block,
                        win_probabilities)

CASOS = [
    (36, 120, 42, 100), (70, 140, 45, 200), (25, 100, 25, 100),
    (90, 200, 70, 150), (40, 110, 55, 90), (50, 150, 45, 160),
    (33, 140, 38, 120), (53, 100, 53, 100),
]


def test_the_table_matches_the_scalar_reference():
    tabela = ko_table()
    for damage, hp, hits in ((36, 100, 3), (53, 100, 2), (70, 190, 3), (120, 400, 4)):
        assert abs(tabela[damage, hits, hp] - probability_of_ko(damage, hp, hits)) < 1e-6


def test_the_table_knows_about_multi_hit_moves():
    tabela = ko_table(HITS_TWO_TO_FIVE)
    for damage, hp, turns in ((25, 120, 3), (10, 100, 4), (50, 300, 3)):
        esperado = probability_of_ko_multi(damage, hp, turns, HITS_TWO_TO_FIVE)
        assert abs(tabela[damage, turns, hp] - esperado) < 1e-6


@pytest.mark.parametrize("speed,ospeed", [(40, 60), (60, 40), (50, 50)])
def test_the_vectorized_score_matches_the_scalar_engine(speed, ospeed):
    damage, hp, odamage, ohp = (np.array(c) for c in zip(*CASOS))
    rapido = np.full(len(CASOS), speed)
    lento = np.full(len(CASOS), ospeed)
    vetor = win_probabilities(damage, hp, odamage, ohp, rapido, lento)
    for i, (d, h, od, oh) in enumerate(CASOS):
        escalar = win_probability(Combatant(damage=d, hp=h, speed=speed),
                                  Combatant(damage=od, hp=oh, speed=ospeed),
                                  max_turns=6)
        assert abs(vetor[i] - escalar) < 1e-6, CASOS[i]


def test_damage_above_the_table_is_still_a_guaranteed_ohko():
    # Acima do limite da tabela o dano minimo ja passa o HP maximo, logo
    # cortar e exato e nao uma aproximacao.
    assert MAX_DAMAGE * 85 // 100 >= MAX_HP
    tabela = ko_table()
    enorme = np.array([MAX_DAMAGE * 3])
    um = np.array([1])
    cem = np.array([MAX_HP])
    assert win_probabilities(enorme, cem, um, cem, um, um)[0] == 1.0


def test_the_blocked_path_agrees_with_the_general_one():
    # No batch o atacante e fixo por bloco: o seu dano, HP e ordem de ataque
    # sao escalares, e a tabela colapsa numa fatia de 7x701 que cabe em cache.
    # Mede 1.5x10^7/s contra 7x10^6/s, logo tem de dar o mesmo numero.
    tabela = ko_table()
    odamage = np.arange(20, 220)
    ohp = np.arange(100, 300)
    bloco = win_block(137, 320, odamage, ohp, 1.0, tabela)
    geral = win_probabilities(np.full(len(odamage), 137), np.full(len(ohp), 320),
                              odamage, ohp,
                              np.full(len(ohp), 99), np.ones(len(ohp)), tabela)
    assert np.abs(bloco - geral).max() < 1e-6


def test_the_blocked_path_handles_losing_the_speed_tie():
    # Trocas apertadas: num matchup ja decidido a ordem nao muda nada.
    tabela = ko_table()
    odamage, ohp = np.arange(40, 90), np.arange(150, 200)
    lento = win_block(60, 120, odamage, ohp, 0.0, tabela)
    rapido = win_block(60, 120, odamage, ohp, 1.0, tabela)
    assert (rapido >= lento).all() and (rapido > lento).any()


def test_the_cell_carries_the_hp_left_as_well_as_the_win():
    # A moeda da sobrevivencia e o HP com que fico (CONTEXT.md 3.6b). Sai do
    # mesmo caminho vectorizado e e conferido contra o motor exacto.
    from mon.sequence import Fighter, resolve
    from mon.vector import trade
    tabela = ko_table()
    casos = [(70, 300, 40, 190, True), (60, 200, 45, 160, True),
             (36, 120, 42, 100, False), (90, 250, 55, 200, True),
             (80, 220, 60, 240, True)]
    for damage, hp, odamage, ohp, primeiro in casos:
        exacto = resolve(Fighter(damage=damage, hp=hp, speed=60 if primeiro else 40),
                         Fighter(damage=odamage, hp=ohp, speed=50))
        pwin, ehp = trade(damage, hp, np.array([odamage]), np.array([ohp]),
                          1.0 if primeiro else 0.0, tabela)
        assert abs(pwin[0] - exacto.survival) < 1e-6
        assert abs(ehp[0] - exacto.expected_hp()) < 1.0


def test_the_hp_left_is_zero_when_i_never_win():
    from mon.vector import trade
    pwin, ehp = trade(1, 100, np.array([900]), np.array([700]), 0.0)
    assert pwin[0] == 0.0 and ehp[0] == 0.0


def test_attack_order_can_vary_per_defender():
    # Uns defensores sao mais rapidos que eu e outros nao. Antes isto obrigava
    # a separar o pool em ramos; agora entra como array.
    from mon.vector import trade
    odamage = np.array([45, 45, 45])
    ohp = np.array([200, 200, 200])
    misto = trade(60, 150, odamage, ohp, np.array([1.0, 0.5, 0.0]))
    primeiro = trade(60, 150, odamage, ohp, 1.0)
    segundo = trade(60, 150, odamage, ohp, 0.0)
    assert abs(misto[0][0] - primeiro[0][0]) < 1e-6
    assert abs(misto[0][2] - segundo[0][2]) < 1e-6
    assert primeiro[0][1] >= misto[0][1] >= segundo[0][1]
    assert abs(misto[0][1] - (primeiro[0][1] + segundo[0][1]) / 2) < 1e-6
