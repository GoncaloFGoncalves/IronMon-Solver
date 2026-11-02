"""Mons seguidos por checkpoint -- o denominador do relogio do status."""

import pytest

from mon.abilities import guts_feasibility
from mon.gauntlet import ELITE_FOUR_MONS, checkpoint_mons
from mon.trainers import SPLITS, load_trainers


@pytest.fixture(scope="module")
def trainers():
    return load_trainers()


def test_every_checkpoint_has_a_count(trainers):
    for checkpoint in SPLITS:
        assert checkpoint_mons(checkpoint, trainers) >= 1


def test_a_gym_checkpoint_is_its_room(trainers):
    from mon.gauntlet import stages_of, mon_count
    for checkpoint in ("brock", "erika", "giovanni"):
        assert (checkpoint_mons(checkpoint, trainers)
                == mon_count(stages_of(checkpoint, trainers)))


def test_the_elite_four_is_not_in_the_map_data(trainers):
    # O FRLGIronmonMap tem a Victory Road mas nao os cinco do Elite 4. O
    # numero e dado, nao derivado -- 5 treinadores x 6 mons.
    from mon.gauntlet import GYM_AREAS
    assert "elite-4" not in GYM_AREAS
    assert ELITE_FOUR_MONS == 30
    assert checkpoint_mons("elite-4", trainers) == ELITE_FOUR_MONS


def test_the_elite_four_is_the_longest_run_without_healing(trainers):
    contagens = {c: checkpoint_mons(c, trainers) for c in SPLITS}
    assert contagens["elite-4"] == max(contagens.values())
    assert contagens["brock"] == 7


def test_guts_is_worthless_in_the_elite_four(trainers):
    # 30 mons sao ~90 turnos, e o burn tira 1/8 por turno: mesmo com OHKO em
    # tudo sao 30 turnos, quase quatro vezes o HP maximo. O status tem de
    # cair nos ultimos dois mons para se chegar ao fim.
    brock = guts_feasibility(checkpoint_mons("brock", trainers))
    elite = guts_feasibility(checkpoint_mons("elite-4", trainers))
    assert brock > 0.10
    assert elite < 0.001
    assert brock / elite > 100


def test_an_unknown_checkpoint_is_an_error(trainers):
    with pytest.raises(KeyError):
        checkpoint_mons("viridian-forest", trainers)
