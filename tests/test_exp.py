from mon.exp import (CURVES, exp_from_defeating, level_at, thresholds)


def test_the_six_gen_3_curves_are_all_mapped():
    assert set(CURVES) == {"MEDIUM_FAST", "MEDIUM_SLOW", "SLOW", "FAST",
                           "ERRATIC", "FLUCTUATING"}


def test_the_curves_are_the_published_totals_at_level_100():
    # Valores canonicos de Gen 3: e por aqui que se confere a tabela toda.
    assert thresholds("MEDIUM_FAST")[100] == 1_000_000
    assert thresholds("FAST")[100] == 800_000
    assert thresholds("SLOW")[100] == 1_250_000
    assert thresholds("MEDIUM_SLOW")[100] == 1_059_860
    assert thresholds("ERRATIC")[100] == 600_000
    assert thresholds("FLUCTUATING")[100] == 1_640_000


def test_level_one_costs_nothing_on_every_curve():
    assert all(thresholds(curve)[1] == 0 for curve in CURVES)


def test_the_level_is_the_last_threshold_crossed():
    curve = "MEDIUM_FAST"
    assert level_at(curve, 0) == 1
    assert level_at(curve, thresholds(curve)[10]) == 10
    assert level_at(curve, thresholds(curve)[10] - 1) == 9
    assert level_at(curve, 10 ** 9) == 100


def test_a_trainer_mon_is_worth_half_again_as_much():
    # Gen 3: exp = base x nivel / 7, e os treinadores dao 1.5x.
    assert exp_from_defeating(64, 20, trainer=False) == 64 * 20 // 7
    assert exp_from_defeating(64, 20) == (64 * 20 // 7) * 3 // 2


def test_exp_scales_with_the_level_of_what_i_beat():
    assert (exp_from_defeating(100, 40) > exp_from_defeating(100, 20)
            > exp_from_defeating(100, 10))
