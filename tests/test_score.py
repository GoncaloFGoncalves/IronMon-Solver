from mon.dex import Species
from mon.moves import Move
from mon.pool import DefenderPool
from mon.score import Cell, score_variant
from mon.upside import Upside
from mon.variants import variants

SNORLAX = Species(143, "snorlax", ("NORMAL",), 540)
GENGAR = Species(94, "gengar", ("GHOST", "POISON"), 500)

POOL = [
    Move("body-slam", "NORMAL", 85, pp=15),
    Move("surf", "WATER", 95, pp=15),
    Move("thunderbolt", "ELECTRIC", 95, pp=15),
    Move("earthquake", "GROUND", 100, pp=10),
    Move("shadow-ball", "GHOST", 80, pp=15),
]


def defensores(level=50):
    return DefenderPool(variants(SNORLAX, level, 31)[:5]
                        + variants(GENGAR, level, 31)[:5])


def test_a_cell_carries_the_win_and_the_hp_left():
    atacante = variants(SNORLAX, 50, 31)[0]
    cell = score_variant(atacante, POOL, defensores())
    assert isinstance(cell, Cell)
    assert 0 <= cell.win <= 1 and cell.hp_left >= 0


def test_a_normal_only_mon_cannot_touch_a_ghost():
    atacante = variants(SNORLAX, 50, 31)[0]
    fantasmas = DefenderPool(variants(GENGAR, 50, 31)[:5])
    assert score_variant(atacante, [POOL[0]], fantasmas).win == 0.0
    assert score_variant(atacante, [POOL[0], POOL[4]], fantasmas, known=2).win > 0


def test_knowing_more_moves_can_only_help():
    atacante = variants(SNORLAX, 50, 31)[0]
    alvos = defensores()
    scores = [score_variant(atacante, POOL, alvos, known=n).win
              for n in (1, 2, 4, 5)]
    assert scores == sorted(scores)


def test_knowing_one_move_is_the_pool_average():
    # Com um move so, o esperado e a media simples sobre os moves do pool.
    atacante = variants(SNORLAX, 50, 31)[0]
    alvos = defensores()
    um = score_variant(atacante, POOL, alvos, known=1).win
    cada = [score_variant(atacante, [move], alvos, known=1).win for move in POOL]
    assert abs(um - sum(cada) / len(cada)) < 1e-9


def test_a_dead_ability_drags_the_cell_down():
    atacante = variants(SNORLAX, 50, 31)[0]
    alvos = defensores()
    assert (score_variant(atacante, POOL, alvos, ability="truant").win
            < score_variant(atacante, POOL, alvos).win)


def test_a_secondary_effect_lifts_the_move_that_has_it():
    atacante = variants(SNORLAX, 50, 31)[0]
    alvos = defensores()
    sem = score_variant(atacante, POOL, alvos, known=1)
    com = score_variant(atacante, POOL, alvos, known=1,
                        upsides={"thunderbolt": Upside("paralysis", 0.10)})
    assert com.win >= sem.win


def test_the_cell_records_how_many_moves_it_assumed():
    atacante = variants(SNORLAX, 50, 31)[0]
    assert score_variant(atacante, POOL, defensores(), known=3).known == 3
    assert score_variant(atacante, POOL[:2], defensores(), known=4).known == 2
