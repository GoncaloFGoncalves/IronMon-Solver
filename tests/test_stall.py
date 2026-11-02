"""A parede: um adversario que eu nao consigo ferir, e que se resolve a PP."""

import pytest

from mon.stall import (STRUGGLE_POWER, STRUGGLE_RECOIL, Wall, resolve,
                       no_coverage_chance)


def wall(**kwargs) -> Wall:
    base = dict(my_hp=200, my_pp=60, their_hp=1, their_damage=10,
                their_pp=60, struggle=40)
    base.update(kwargs)
    return Wall(**base)

@pytest.fixture
def party_pieces():
    """Um embate de 6, com os cinco normais todos iguais ao mediano."""
    return dict(
        my_hp=200, my_pp=60, my_damage=70, my_speed=120,
        my_struggle=40,
        # `their_pp=10` de proposito: com os 60 de quatro moves o stall e
        # impossivel em qualquer slot, e a posicao deixa de se ver. Com 10 o
        # embate e ganhavel a cheio e perdido a meio -- que e o ponto.
        their_hp=1, their_damage=10, their_pp=10, their_struggle=10,
        other_hp=120, other_damage=18, other_speed=60,
    )


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


def test_a_wall_with_no_damaging_moves_costs_exactly_one_struggle():
    # Bolas infinitas: se ele nao tem moves de dano, da Struggle no primeiro
    # turno, leva 1/4 de recuo e morre. O custo e o dano de UM Struggle dele,
    # nao de um ataque normal -- sao coisas diferentes.
    out = resolve(wall(their_pp=0, their_damage=99, their_struggle=20))
    assert out.survival == 1.0
    assert out.turns == 1
    assert out.struggled == "them"
    # Perdi um Struggle dele (base 20, logo 17 a 20), nao os 99 do ataque
    # que ele nao tem.
    assert 200 - 21 <= out.hp_left <= 200 - 16


def test_a_wall_with_no_damaging_moves_can_still_kill_a_weak_mon():
    out = resolve(wall(my_hp=12, their_pp=0, their_struggle=40))
    assert out.survival < 1.0


def test_the_struggle_damage_defaults_to_their_normal_damage():
    # Sem valor explicito assume-se o mesmo: e conservador e nao inventa.
    a = resolve(wall(their_pp=0, their_damage=30))
    b = resolve(wall(their_pp=0, their_damage=30, their_struggle=30))
    assert a == b


def test_the_wall_position_changes_the_outcome(party_pieces):
    # A pergunta: o Shedinja ao slot 1 e ao slot 6 nao sao o mesmo embate.
    from mon.stall import party_outcome
    kit = party_pieces
    primeiro = party_outcome(wall_at=1, size=6, **kit)
    ultimo = party_outcome(wall_at=6, size=6, **kit)
    assert primeiro.survival != ultimo.survival
    # Ao slot 1 chego inteiro mas saio sem PP para os outros cinco; ao slot 6
    # chego gasto mas nao sobra nada para lutar depois.
    assert primeiro.struggling_after > 0
    assert ultimo.struggling_after == 0


def test_every_position_is_resolvable(party_pieces):
    from mon.stall import party_outcome
    kit = party_pieces
    for slot in range(1, 7):
        out = party_outcome(wall_at=slot, size=6, **kit)
        assert 0.0 <= out.survival <= 1.0
        assert out.struggling_after == 6 - slot


def test_a_position_outside_the_party_is_an_error(party_pieces):
    from mon.stall import party_outcome
    kit = party_pieces
    for slot in (0, 7):
        with pytest.raises(ValueError):
            party_outcome(wall_at=slot, size=6, **kit)


def test_the_wall_is_survivable_only_in_the_last_slot(party_pieces):
    # O resultado que surpreende: nao e o embate com a parede que mata, e o
    # que vem depois. Ganha-se a parede e fica-se sem PP; os que faltam
    # fazem-se a Struggle, com 1/4 de recuo por golpe, e isso mata.
    from mon.stall import party_outcome
    kit = party_pieces
    por_slot = [party_outcome(wall_at=n, size=6, **kit).survival
                for n in range(1, 7)]
    assert por_slot[-1] > 0.5, por_slot
    assert all(v == 0.0 for v in por_slot[:-1]), por_slot


def test_a_lone_wall_is_won_whatever_the_slot(party_pieces):
    # Com equipa de 1 nao ha "depois", logo o slot nao muda nada.
    from mon.stall import party_outcome
    kit = party_pieces
    out = party_outcome(wall_at=1, size=1, **kit)
    assert out.survival > 0.5
    assert out.struggling_after == 0
