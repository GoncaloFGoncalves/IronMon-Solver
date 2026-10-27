import numpy as np

from mon.orderstat import expected_best, subset_weights


def test_the_weights_are_a_probability_distribution():
    w = subset_weights(10, 4)
    assert len(w) == 10
    assert abs(w.sum() - 1.0) < 1e-12
    assert (w >= 0).all()


def test_a_move_cannot_be_the_best_if_too_few_are_below_it():
    # Com 4 moves conhecidos, os 3 piores do pool nunca podem ser o melhor
    # dos 4: nao ha 3 piores que eles para completar o conjunto.
    w = subset_weights(10, 4)
    assert (w[:3] == 0).all()
    assert w[3] > 0


def test_knowing_every_move_means_the_best_is_the_best():
    w = subset_weights(6, 6)
    assert w[-1] == 1.0 and w[:-1].sum() == 0.0


def test_knowing_one_move_is_the_plain_average():
    w = subset_weights(5, 1)
    assert np.allclose(w, 0.2)


def test_more_known_moves_can_only_help():
    scores = np.array([[0.1], [0.4], [0.5], [0.9]])
    um = expected_best(scores, known=1)[0]
    dois = expected_best(scores, known=2)[0]
    quatro = expected_best(scores, known=4)[0]
    assert um < dois < quatro == 0.9


def test_the_companion_value_follows_the_chosen_move_not_its_own_maximum():
    # Escolhe-se o move pelo win; o HP que fica e o **daquele** move, nao o
    # melhor HP de todos.
    win = np.array([[0.2], [0.9]])
    hp = np.array([[0.8], [0.1]])
    melhor_win, hp_junto = expected_best(win, known=2, companion=hp)
    assert melhor_win[0] == 0.9
    assert hp_junto[0] == 0.1
