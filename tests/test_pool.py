import numpy as np

from mon.dex import Species
from mon.moves import Move
from mon.pool import DefenderPool
from mon.variants import attack_damage, variants

SNORLAX = Species(143, "snorlax", ("NORMAL",), 540)
GENGAR = Species(94, "gengar", ("GHOST", "POISON"), 500)
MOVES = [Move("body-slam", "NORMAL", 85, pp=15),
         Move("surf", "WATER", 95, pp=15),
         Move("shadow-ball", "GHOST", 80, pp=15),
         Move("earthquake", "GROUND", 100, pp=10)]


def defensores():
    return variants(SNORLAX, 50, 31)[:6] + variants(GENGAR, 50, 31)[:6]


def test_the_matrix_matches_the_scalar_damage_one_cell_at_a_time():
    # O caminho rapido tem de dar exatamente o mesmo que o escalar: e a
    # aritmetica inteira do jogo, nao uma aproximacao.
    alvos = defensores()
    pool = DefenderPool(alvos)
    atacante = variants(SNORLAX, 50, 31)[0]
    matriz = pool.damage_matrix(atacante, MOVES)
    assert matriz.shape == (len(MOVES), len(alvos))
    for i, move in enumerate(MOVES):
        for j, defender in enumerate(alvos):
            assert matriz[i, j] == attack_damage(atacante, defender,
                                                 move.power, move.type)


def test_immunity_shows_up_as_zero():
    pool = DefenderPool(variants(GENGAR, 50, 31)[:6])
    atacante = variants(SNORLAX, 50, 31)[0]
    matriz = pool.damage_matrix(atacante, MOVES)
    normal = MOVES.index(MOVES[0])
    assert (matriz[normal] == 0).all(), "NORMAL nao toca GHOST"


def test_the_pool_precomputes_what_every_attacker_reuses():
    alvos = defensores()
    pool = DefenderPool(alvos)
    assert pool.defense.shape == (len(alvos),)
    assert pool.hp.shape == (len(alvos),)
    # 17 tipos x defensores: calcula-se uma vez por checkpoint.
    assert pool.effectiveness.shape[0] == 17
