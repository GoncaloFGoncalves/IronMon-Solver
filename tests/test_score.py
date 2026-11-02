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
    # O pool de ameaca tem de ser o mesmo nos dois lados: o que eu sei nao
    # muda os 4 moves que ele pode ter sorteado.
    um = score_variant(atacante, POOL, alvos, known=1, threat_moves=POOL).win
    cada = [score_variant(atacante, [move], alvos, known=1,
                          threat_moves=POOL).win for move in POOL]
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


def _setup():
    from mon.pool import DefenderPool
    from mon.veekun import load_moves, load_species
    from mon.variants import variants
    species = load_species()
    moves = [m for m in load_moves() if m.kind == "power" and m.power]
    pool = DefenderPool([v for o in species for v in variants(o, 56, 31)])
    return species, moves, pool


def test_the_kernel_weighs_the_lethal_draw_against_the_safe_one():
    # 4b: a troca resolve-se duas vezes, nao uma. A celula tem de ficar entre
    # os dois extremos -- o cenario em que ele tirou um move que me mata e o
    # cenario em que nao tirou.
    import numpy as np
    from mon.incoming import incoming_profile, lethal_cap
    from mon.score import score_variant, _scenario_cells
    from mon.variants import variants
    species, moves, pool = _setup()
    one = [s for s in species if s.name == "gyarados"][0]
    me = [v for v in variants(one, 70, 27)
          if v.profile == ("physical", "def_tank", "fast")][0]

    share, safe = incoming_profile(me, moves, pool)
    assert 0.0 < share.mean() < 1.0, "o fixture tem de ter os dois cenarios"
    cell = score_variant(me, moves, pool, known=19)
    letal, seguro = _scenario_cells(me, moves, pool, known=19)
    assert letal.win < cell.win < seguro.win


def test_a_four_times_weakness_now_costs_something():
    # O teste que o modelo antigo nao podia passar: Gyarados e Snorlax, mesmo
    # BST e mesmo perfil, davam a mesma celula do lado defensivo.
    from mon.score import score_variant
    from mon.variants import variants
    species, moves, pool = _setup()
    cells = {}
    for name in ("gyarados", "snorlax"):
        one = [s for s in species if s.name == name][0]
        me = [v for v in variants(one, 70, 27)
              if v.profile == ("physical", "def_tank", "fast")][0]
        cells[name] = score_variant(me, moves, pool, known=19)
    assert cells["gyarados"].win < cells["snorlax"].win


def test_the_cell_carries_the_lethal_share():
    # O `hp_left` e condicional a ganhar, por isso sobe quando o risco passa
    # a ser binario: as vitorias que restam sao as folgadas. Sem a quota
    # letal a celula diria que o mon fragil esta melhor do que o solido.
    from mon.score import score_variant
    from mon.variants import variants
    species, moves, pool = _setup()
    cells = {}
    for name in ("gyarados", "snorlax"):
        one = [s for s in species if s.name == name][0]
        me = [v for v in variants(one, 70, 27)
              if v.profile == ("physical", "def_tank", "fast")][0]
        cells[name] = score_variant(me, moves, pool, known=19)
    # O Gyarados (x4 a ELECTRIC) parece melhor pelo HP e e pior pelo risco.
    assert cells["gyarados"].hp_left > cells["snorlax"].hp_left
    assert cells["gyarados"].risk > cells["snorlax"].risk
    for cell in cells.values():
        assert 0.0 <= cell.risk <= 1.0
