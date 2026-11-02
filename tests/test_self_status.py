"""A viabilidade do Guts cresce com o tamanho da dungeon."""

import pytest

from mon.abilities import STATUS_PER_MON, self_status, utilization, MonContext
from mon.battle import Combatant
from mon.gauntlet import DUNGEON_AREAS, dungeon_mons
from mon.trainers import load_trainers


@pytest.fixture(scope="module")
def trainers():
    return load_trainers()


def test_every_dungeon_section_has_a_mon_count(trainers):
    from mon.dungeons import DUNGEONS
    sections = {d.name for d in DUNGEONS}
    for section in sections:
        assert dungeon_mons(section, trainers) >= 1


def test_the_elite_four_is_the_one_section_without_a_map_area(trainers):
    # O FRLGIronmonMap tem a Victory Road e nao tem os cinco do Elite 4, logo
    # a contagem dele e dada em vez de derivada -- e e a unica assim.
    from mon.dungeons import DUNGEONS
    sections = {d.name for d in DUNGEONS}
    assert sections - set(DUNGEON_AREAS) == {"elite-4"}
    assert dungeon_mons("elite-4", trainers) == 30


def test_a_gym_counts_its_whole_room(trainers):
    # Regra do desafio: dentro de um ginasio luta-se com todos.
    assert dungeon_mons("pewter-gym", trainers) == 7
    assert dungeon_mons("celadon-gym", trainers) == 24
    assert dungeon_mons("viridian-gym", trainers) == 30


def test_a_non_gym_counts_only_the_mandatory_path(trainers):
    # Fora dos ginasios os treinadores evitam-se, e o trade-off e o nivel.
    # Nao se sabe **quais** sao os obrigatorios, so quantos -- logo estima-se
    # pelo tamanho medio de equipa daquela area.
    from mon.dungeons import mandatory_battles
    silph = dungeon_mons("silph-co", trainers)
    assert mandatory_battles("silph-co") == 4
    assert 4 <= silph < 93, "4 embates, nao os 93 mons da torre toda"


def test_the_per_mon_chance_is_derived_from_the_move_pool():
    # O 0.25 que aqui estava era um palpite. Isto re-deriva-o dos dados: dos
    # 194 moves de dano, 27 dao um status que o Guts aproveita.
    from math import comb
    from statistics import mean
    from mon.upside import TURNS
    from mon.veekun import load_moves, load_upside
    moves = [m for m in load_moves() if m.kind == "power" and m.power]
    upsides = load_upside()
    useful = [upsides[m.name].chance for m in moves
              if m.name in upsides
              and upsides[m.name].ailment in {"burn", "poison", "paralysis"}
              and upsides[m.name].chance]
    assert len(useful) == 27
    has = 1 - comb(len(moves) - len(useful), 4) / comb(len(moves), 4)
    lands = mean(1 - (1 - c) ** TURNS for c in useful)
    assert abs(STATUS_PER_MON - has * lands) < 5e-4


def test_the_chance_grows_with_the_dungeon():
    valores = [self_status(n) for n in (1, 2, 7, 20, 30)]
    assert valores == sorted(valores)
    assert abs(valores[0] - STATUS_PER_MON) < 1e-12
    assert self_status(7) > 0.8
    assert self_status(30) > 0.99


def test_one_mon_is_the_floor_and_zero_is_an_error():
    assert self_status(1) == STATUS_PER_MON
    with pytest.raises(ValueError):
        self_status(0)




def test_an_ability_without_feasibility_ignores_the_dungeon():
    me = Combatant(damage=36.0, hp=120.0, speed=100.0)
    them = Combatant(damage=42.0, hp=100.0, speed=80.0)
    ctx = MonContext(me=me, them=them, physical=True)
    assert (utilization("truant", ctx, mons=7)
            == utilization("truant", ctx, mons=30))


def test_guts_feasibility_falls_with_the_dungeon_not_rises():
    # O erro que isto corrige: `self_status` cresce com a fila, e por isso o
    # modelo dizia que o Guts era melhor numa sala de 30 do que numa de 2.
    # E o contrario -- o burn tira 1/8 por turno e nao ha cura, logo quanto
    # mais mons faltam depois do status, mais certo e nao chegar ao fim.
    from mon.abilities import guts_feasibility
    valores = [guts_feasibility(n) for n in (2, 3, 7, 12, 30)]
    assert valores == sorted(valores, reverse=True)
    assert valores[0] > 0.4 and valores[-1] < 0.001


def test_a_single_mon_fight_is_pure_status_chance():
    # Com um mon so nao ha "depois": a viabilidade e a propria hipotese de
    # apanhar o status.
    from mon.abilities import guts_feasibility
    assert abs(guts_feasibility(1) - STATUS_PER_MON) < 1e-12


def test_feasibility_never_exceeds_the_chance_of_being_statused():
    from mon.abilities import guts_feasibility
    for n in (1, 2, 5, 7, 20, 30):
        assert guts_feasibility(n) <= self_status(n) + 1e-12


def test_the_burn_clock_kills_before_the_room_ends():
    # A aritmetica do problema: queimado ao primeiro mon de uma fila de 6,
    # sem OHKOs, morre-se ao terceiro.
    from mon.abilities import BURN_RESIDUAL
    from mon.upside import TURNS
    assert 1 - 2 * TURNS * BURN_RESIDUAL == 0.25
    assert 1 - 3 * TURNS * BURN_RESIDUAL <= 0


def test_guts_is_worth_less_in_a_longer_dungeon():
    # Substitui a expectativa anterior, que estava invertida.
    me = Combatant(damage=36.0, hp=120.0, speed=100.0)
    them = Combatant(damage=42.0, hp=100.0, speed=80.0)
    ctx = MonContext(me=me, them=them, physical=True)
    assert utilization("guts", ctx, mons=7) > utilization("guts", ctx, mons=30)
