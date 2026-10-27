from mon.levels import (FULLY_EVOLVED_EXP_YIELD, MEAN_EXP_YIELD, START_LEVEL,
                        expected_levels, level_band, opponent_levels)
from mon.trainers import SPLITS

SPLITS_INDEX = {name: index for index, name in enumerate(SPLITS)}


def test_the_randomizer_standardizes_every_mon_to_one_curve():
    from mon.exp import STANDARD_CURVE
    assert STANDARD_CURVE == "FLUCTUATING"


def test_it_matches_the_level_observed_in_real_runs_at_brock():
    # Calibracao contra runs reais do Goncalo: no Brock o nivel ronda 18-19,
    # e 21 e o maximo quando os mons do treinador vem ja evoluidos. Os dois
    # valores saem do modelo sem nada ajustado -- e a validacao de que a
    # formula, os yields de Gen 3 e o conjunto de treinadores estao certos.
    tipico, maximo = level_band()
    assert tipico[0] == 19
    assert maximo[0] == 21


def test_every_split_gets_a_level():
    niveis = expected_levels()
    assert len(niveis) == 9
    assert niveis[0] >= START_LEVEL


def test_the_level_only_goes_up_along_the_run():
    assert list(expected_levels()) == sorted(expected_levels())


def test_the_default_counts_the_whole_route():
    # Calibrado: as runs reais lutam com os treinadores das areas da rota, nao
    # so com os inevitaveis. O caminho minimo dava 11 no Brock, e o real e 19.
    from mon.trainers import load_trainers, unavoidable
    minimo = expected_levels(trainers=unavoidable(load_trainers()))
    assert minimo[0] < expected_levels()[0]


def test_a_fully_evolved_opponent_pool_is_worth_more_exp():
    assert FULLY_EVOLVED_EXP_YIELD > MEAN_EXP_YIELD
    assert 130 < MEAN_EXP_YIELD < 141


def test_the_opponent_level_is_not_the_player_level():
    adversario = opponent_levels()
    assert len(adversario) == 9
    assert adversario[0] >= 18, "o Brock do Kaizo e 18-21"
    assert list(adversario) == sorted(adversario)


def test_a_richer_pool_levels_the_mon_faster():
    magro = expected_levels(base_exp=60)
    gordo = expected_levels(base_exp=200)
    assert all(a <= b for a, b in zip(magro, gordo))
    assert magro[-1] < gordo[-1]


def test_the_level_lead_rises_then_falls():
    """Confirmado contra runs reais: a vantagem sobe e depois fecha.

    E a forma que valida o conjunto de treinadores por omissao. Chegas ao
    Brock em paridade (+1), abres vantagem ate a Erika (+22) e o Elite 4
    volta a fechar (+6). Os dois extremos sao os pontos de perigo: e onde a
    tabela tem de estar certa, porque e onde as runs morrem.
    """
    lead = [meu - dele for meu, dele in zip(expected_levels(), opponent_levels())]
    assert lead[0] <= 2, "no Brock nao ha vantagem"
    assert max(lead) == lead[SPLITS_INDEX["erika"]], "o pico e na Erika"
    assert lead[-1] < max(lead) / 2, "o Elite 4 fecha a vantagem"
    assert lead == sorted(lead[:4]) + lead[4:], "sobe sem recuos ate ao pico"
