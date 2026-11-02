"""Um ginasio e uma fila sem cura, nao uma batalha."""

import pytest

from mon.gauntlet import (GYM_AREAS, Stage, gauntlet, mon_count,
                          leader_only, stages_of)
from mon.trainers import LEADERS, load_trainers


@pytest.fixture(scope="module")
def trainers():
    return load_trainers()


def test_every_checkpoint_gym_is_mapped():
    # Os 8 ginasios de Kanto; o Elite 4 nao e um ginasio e nao entra aqui.
    assert len(GYM_AREAS) == 8
    assert GYM_AREAS["brock"] == "Pewter Gym"


def test_the_leader_comes_last(trainers):
    for checkpoint in GYM_AREAS:
        stages = stages_of(checkpoint, trainers)
        assert stages[-1].trainer in LEADERS
        assert not any(s.trainer in LEADERS for s in stages[:-1])


def test_pewter_is_the_camper_then_brock(trainers):
    stages = stages_of("brock", trainers)
    assert [s.trainer for s in stages] == ["Camper Liam", "Brock"]
    assert [len(s.levels) for s in stages] == [2, 5]
    assert mon_count(stages) == 7


def test_the_gym_is_longer_than_the_leader_alone(trainers):
    # O ponto todo: contar so o lider subestima a fila em toda a parte.
    for checkpoint in GYM_AREAS:
        inteiro = mon_count(stages_of(checkpoint, trainers))
        so_lider = mon_count(leader_only(checkpoint, trainers))
        assert inteiro > so_lider
    assert mon_count(stages_of("erika", trainers)) == 24
    assert mon_count(leader_only("erika", trainers)) == 6


def test_the_gauntlet_flattens_the_stages_into_one_queue(trainers):
    fila = gauntlet("brock", trainers)
    assert len(fila) == 7
    # Os niveis vem pela ordem em que se lutam: o campista antes do lider.
    assert fila[:2] == [15, 17]
    assert fila[-1] == 21


def test_an_unknown_checkpoint_is_an_error(trainers):
    with pytest.raises(KeyError):
        stages_of("elite-4", trainers)


def test_a_stage_keeps_the_levels_it_came_with(trainers):
    stages = stages_of("surge", trainers)
    assert all(isinstance(s, Stage) and s.levels for s in stages)
    assert mon_count(stages) == sum(len(s.levels) for s in stages)
