"""O dano que levo: moves reais do adversario, com o excesso desperdicado."""

import numpy as np
import pytest

from mon.incoming import SLOTS, lethal_cap, incoming_profile
from mon.pool import DefenderPool
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


def test_the_cap_is_the_smallest_base_damage_that_always_kills():
    # O roll minimo e 85%: abaixo de hp/0.85 ha rolls que nao matam, acima
    # nenhum dano extra pode importar.
    from mon.damage import probability_of_ko
    for hp in (51, 88, 161, 196):
        cap = lethal_cap(hp)
        assert probability_of_ko(cap, hp, 1) == 1.0
        assert probability_of_ko(cap - 1, hp, 1) < 1.0


def test_overkill_is_discarded(setup, moves):
    # O ponto da decisao: um move que faz 3x o meu HP nao vale mais do que um
    # que mata na mesma. Sem o corte, a media do melhor de 4 inflaciona-se.
    attacker, pool = setup
    p, safe, raw = incoming_profile(attacker, moves, pool, detail=True)
    assert raw.max() > 3 * attacker.hp
    assert raw.min() >= 0
    cap = lethal_cap(attacker.hp)
    assert safe.max() <= cap


def test_the_lethal_share_is_a_probability(setup, moves):
    attacker, pool = setup
    p, safe = incoming_profile(attacker, moves, pool)
    assert p.shape == safe.shape == pool.hp.shape
    assert np.all((p >= 0.0) & (p <= 1.0))


def test_a_four_times_weak_target_meets_more_lethal_draws(setup, moves):
    # Gyarados (WATER/FLYING, x4 a ELECTRIC) contra Snorlax (NORMAL), mesmo
    # BST e mesmo perfil: o modelo antigo dava-lhes o mesmo dano recebido.
    species = load_species()
    pool = DefenderPool([v for o in species for v in variants(o, 56, 31)])
    ps = {}
    for name in ("gyarados", "snorlax"):
        one = [s for s in species if s.name == name][0]
        me = [v for v in variants(one, 70, 27)
              if v.profile == ("physical", "def_tank", "fast")][0]
        ps[name], _ = incoming_profile(me, moves, pool)
    assert ps["gyarados"].mean() > ps["snorlax"].mean()


def test_nothing_lethal_leaves_the_share_at_zero(setup, moves):
    # Um alvo com HP absurdo: nenhum move do pool mata de um.
    attacker, pool = setup
    from dataclasses import replace
    tanque = replace(attacker, hp=100000)
    p, safe = incoming_profile(tanque, moves, pool)
    assert np.all(p == 0.0)
    assert np.all(safe > 0)


def test_immunity_survives_even_at_one_hit_point(moves):
    # Com 1 de HP quase tudo mata -- menos os 9 moves GROUND, a que o
    # Gyarados (WATER/FLYING) e imune. A quota letal e exactamente
    # 1 - C(9,4)/C(194,4), e nao 1.
    from dataclasses import replace
    from math import comb
    species = load_species()
    pool = DefenderPool([v for o in species for v in variants(o, 56, 31)])
    one = [s for s in species if s.name == "gyarados"][0]
    frangalho = replace([v for v in variants(one, 70, 27)][0], hp=1)
    ground = sum(1 for m in moves if m.type == "GROUND")
    assert ground == 9
    p, _ = incoming_profile(frangalho, moves, pool)
    esperado = 1 - comb(ground, SLOTS) / comb(len(moves), SLOTS)
    # O melhor caso do atacante e so a imunidade a travar: 9 moves de fora.
    assert abs(p.max() - esperado) < 1e-12
    # Nunca 1: a imunidade nao desaparece por eu estar a 1 de HP.
    assert p.max() < 1.0
    # Contra atacantes fracos ate os tipos que resisto caem abaixo do corte,
    # por isso a quota varia pelo pool em vez de ser constante.
    assert p.min() < esperado


def test_fewer_slots_meet_fewer_lethal_draws(setup, moves):
    attacker, pool = setup
    um, _ = incoming_profile(attacker, moves, pool, slots=1)
    quatro, _ = incoming_profile(attacker, moves, pool, slots=SLOTS)
    assert np.all(quatro >= um)
    assert quatro.mean() > um.mean()


def test_the_lethal_share_matches_a_hypergeometric_count(setup, moves):
    # Diferencial contra a conta directa: 1 - C(M-k, n)/C(M, n), onde k e o
    # numero de moves do pool que matam este alvo de um.
    from math import comb
    from mon.damage import probability_of_ko
    attacker, pool = setup
    p, _, raw = incoming_profile(attacker, moves, pool, detail=True)
    index = int(np.argmax(p))
    k = sum(1 for d in raw[:, index]
            if probability_of_ko(int(d), attacker.hp, 1) == 1.0)
    esperado = 1 - comb(len(moves) - k, SLOTS) / comb(len(moves), SLOTS)
    assert abs(p[index] - esperado) < 1e-12
