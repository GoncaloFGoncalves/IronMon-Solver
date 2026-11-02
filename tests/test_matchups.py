"""O ranking por defensor: o que a media da celula esconde."""

import pytest

from mon.matchups import (Matchup, worst_matchups, per_defender,
                          _resolve)
from mon.pool import DefenderPool
from mon.score import score_variant
from mon.veekun import load_moves, load_species
from mon.variants import variants


@pytest.fixture(scope="module")
def moves():
    return [m for m in load_moves() if m.kind == "power" and m.power]


@pytest.fixture(scope="module")
def setup():
    species = load_species()
    gyarados = [s for s in species if s.name == "gyarados"][0]
    attacker = [v for v in variants(gyarados, 70, 27)
                if v.profile == ("physical", "def_tank", "fast")][0]
    pool = DefenderPool([v for other in species
                         for v in variants(other, 56, 31)])
    return attacker, pool


def test_per_defender_averages_to_the_cell(setup, moves):
    # O invariante que justifica a feature: o vector por defensor ja existe
    # dentro do kernel, e so se perde no `.mean()`. Se a media nao bater, o
    # ranking nao esta a ver a mesma coisa que a tabela.
    attacker, pool = setup
    wins, _ = per_defender(attacker, moves, pool, known=19)
    cell = score_variant(attacker, moves, pool, known=19)
    assert abs(wins.mean() - cell.win) < 1e-9


def test_the_worst_are_sorted_and_no_better_than_the_mean(setup, moves):
    attacker, pool = setup
    worst = worst_matchups(attacker, moves, pool, known=19, limit=20)
    assert len(worst) == 20
    assert [m.win for m in worst] == sorted(m.win for m in worst)
    wins, _ = per_defender(attacker, moves, pool, known=19)
    assert worst[-1].win <= wins.mean()


def test_the_mean_hides_total_losses(setup, moves):
    # Gyarados physical/def_tank/fast tem def=212 e spd=86. A celula da ~0.96
    # e mesmo assim ha defensores onde ganha 0% -- e sao especiais, que e o
    # buraco do perfil. E a razao de ser desta tabela.
    attacker, pool = setup
    cell = score_variant(attacker, moves, pool, known=19)
    worst = worst_matchups(attacker, moves, pool, known=19, limit=20)
    # Com os 4 moves dele sorteados (4b) o fundo da tabela ja nao vai a zero:
    # perde-se quando ele calha em ter a resposta, e nem sempre calha. O que
    # fica e a distancia entre a media e a cauda, que e o que a celula esconde.
    assert cell.win > 0.9
    assert worst[0].win < 0.5
    assert cell.win - worst[0].win > 0.5
    especiais = sum(1 for m in worst
                    if m.defender.special_attack > m.defender.attack)
    assert especiais >= 10


def test_a_fixed_moveset_loses_outright_where_a_random_one_keeps_a_chance(
        setup, moves):
    # Com 19 sorteios ha quase sempre um move que serve, e o pior matchup
    # ainda ganha 5% das vezes. Fixando 3 moves o fundo da tabela vai a zero
    # exacto -- nao e azar, e o moveset nao ter resposta nenhuma.
    attacker, pool = setup
    chosen = [m for m in moves
              if m.name in ("waterfall", "earthquake", "return")]
    aleatorio = worst_matchups(attacker, moves, pool, known=19, limit=1)
    fixo = worst_matchups(attacker, chosen, pool, known=len(chosen), limit=1)
    assert aleatorio[0].win > 0.0
    assert fixo[0].win == 0.0


def test_a_matchup_carries_the_defender_it_refers_to(setup, moves):
    attacker, pool = setup
    worst = worst_matchups(attacker, moves, pool, known=19, limit=3)
    for entry in worst:
        assert isinstance(entry, Matchup)
        assert entry.defender in pool.defenders
        assert 0.0 <= entry.win <= 1.0
        assert entry.damage_dealt >= 0 and entry.damage_taken >= 0


def test_a_fixed_moveset_uses_the_best_of_exactly_those_moves(setup, moves):
    # Com `known` igual ao numero de moves, a estatistica de ordem colapsa no
    # maximo: e o caso do painel de moveset concreto.
    import numpy as np
    from mon.score import blend
    attacker, pool = setup
    chosen = [m for m in moves
              if m.name in ("waterfall", "earthquake", "return", "bite")]
    wins, _, _, _, _ = blend(attacker, chosen, pool, threat_moves=moves)
    direto, _ = per_defender(attacker, chosen, pool, known=len(chosen),
                             threat_moves=moves)
    assert np.allclose(direto, wins.max(axis=0))


def test_the_threat_pool_is_not_my_own_moveset(setup, moves):
    # O que eu sei nao muda os 4 moves que ele pode ter. Com 3 moves meus, o
    # dano que levo tem de ser o mesmo que com 194.
    import numpy as np
    attacker, pool = setup
    chosen = [m for m in moves if m.name in ("waterfall", "earthquake", "return")]
    _, _, _, com = _resolve(attacker, chosen, pool, 3, None, threat_moves=moves)
    _, _, _, sem = _resolve(attacker, moves, pool, 19, None, threat_moves=moves)
    assert np.allclose(com, sem)


def test_limit_is_clamped_to_the_pool(setup, moves):
    attacker, pool = setup
    worst = worst_matchups(attacker, moves, pool, known=19, limit=10 ** 6)
    assert len(worst) == len(pool.defenders)
