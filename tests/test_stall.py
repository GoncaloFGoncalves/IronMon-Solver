"""A parede: um adversario que eu nao consigo ferir, e que se resolve a PP."""

import pytest

from mon.stall import (STRUGGLE_POWER, STRUGGLE_RECOIL, Wall, resolve,
                       no_coverage_chance)


def wall(**kwargs) -> Wall:
    base = dict(my_hp=200, my_pp=60, their_hp=1, their_damage=10,
                their_pp=60, struggle=40)
    base.update(kwargs)
    return Wall(**base)


def test_struggle_in_gen_3_is_a_quarter_of_the_damage_dealt():
    # Nao do HP maximo -- isso e Gen 4 em diante. E e typeless desde Gen 2,
    # logo a Wonder Guard nao o bloqueia e o Ghost nao e imune.
    assert STRUGGLE_RECOIL == 1 / 4
    assert STRUGGLE_POWER == 50


def test_running_out_of_pp_kills_a_one_hit_point_wall():
    # O ponto que inverte a intuicao: ficar sem PP nao e perder. O meu
    # Struggle acerta no Shedinja -- typeless, a Wonder Guard nao o para -- e
    # 1 de HP morre com qualquer coisa.
    out = resolve(wall(my_pp=20, their_pp=60, their_damage=1))
    assert out.survival == 1.0
    assert out.struggled == "me"
    assert out.turns == 21


def test_the_side_with_less_pp_struggles_first():
    assert resolve(wall(my_pp=10, their_pp=60)).struggled == "me"
    assert resolve(wall(my_pp=60, their_pp=10)).struggled == "them"
    # Empate: eu ataco no mesmo turno, e o meu Struggle resolve.
    assert resolve(wall(my_pp=30, their_pp=30)).struggled == "me"


def test_their_struggle_kills_them_by_recoil():
    # Se o PP deles acaba primeiro, eles dao Struggle, levam 1/4 do dano que
    # causaram, e com 1 de HP isso mata-os. Nao preciso de os ferir.
    out = resolve(wall(my_pp=60, their_pp=5, their_damage=4, their_hp=1))
    assert out.struggled == "them"
    assert out.survival == 1.0
    assert out.turns == 6


def test_a_wall_that_hits_hard_kills_me_before_the_pp_runs_out():
    # O stall so funciona se ele quase nao me tocar. Sessenta turnos a 20 de
    # dano sao 1 200: nenhum HP aguenta.
    out = resolve(wall(my_hp=200, my_pp=60, their_pp=60, their_damage=20))
    assert out.survival == 0.0
    assert out.hp_left == 0.0


def test_survival_is_a_probability_not_a_verdict():
    # Com o dano a roçar o HP ao longo dos turnos, o resultado e um roll.
    out = resolve(wall(my_hp=100, my_pp=12, their_pp=60, their_damage=9))
    assert 0.0 < out.survival < 1.0


def test_the_fight_leaves_no_pp_for_the_rest_of_the_dungeon():
    # A conclusao que interessa: ganha-se o embate e sai-se sem PP. Numa
    # seccao sem recarga, o resto faz-se a Struggle -- e e ai que a run acaba,
    # nao no embate.
    out = resolve(wall(my_pp=60, their_pp=90, their_damage=2))
    assert out.survival == 1.0
    assert out.pp_left == 0
    assert out.turns == 61


def test_outside_a_dungeon_only_survival_matters():
    # Fora de uma dungeon cura-se e recarrega-se: o custo em HP e PP nao
    # viaja, logo a mesma parede e so "sobrevivo ou nao".
    apertado = wall(my_hp=100, my_pp=40, their_pp=60, their_damage=3)
    out = resolve(apertado)
    # Nao e 1.0 exacto: 41 turnos de dano base 3 dao entre 82 e 123, logo os
    # rolls altos matam. E o tipo de cauda que uma media esconderia.
    assert out.survival > 0.999 and out.survival < 1.0
    assert out.pp_left == 0
    assert 0 < out.hp_left < apertado.my_hp


def test_a_wall_i_can_hurt_is_not_a_wall():
    with pytest.raises(ValueError):
        resolve(wall(struggle=0))


def test_no_coverage_chance_is_hypergeometric():
    from math import comb
    # Dos 194 moves de dano, 72 nao afectam BUG/GHOST (NORMAL e FIGHTING).
    assert abs(no_coverage_chance(72, 194, 4) - comb(72, 4) / comb(194, 4)) < 1e-15
    assert no_coverage_chance(72, 194, 4) > no_coverage_chance(72, 194, 10)
    # Mais moves conhecidos que inuteis no pool: impossivel ficar sem nada.
    assert no_coverage_chance(3, 194, 10) == 0.0
