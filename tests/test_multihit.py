from mon.damage import HITS_TWO_TO_FIVE, probability_of_ko, probability_of_ko_multi


def test_a_single_hit_move_is_the_old_behaviour():
    assert (probability_of_ko_multi(53, 100, 2, {1: 1.0})
            == probability_of_ko(53, 100, 2))


def test_two_fixed_hits_are_two_strikes_per_turn():
    # Double-kick: dois golpes por turno, cada um truncado sozinho. Um turno
    # de 2 golpes nao e um golpe de dano dobrado.
    assert (probability_of_ko_multi(30, 100, 2, {2: 1.0})
            == probability_of_ko(30, 100, 4))


def test_the_gen_3_distribution_is_two_and_three_hits_most_of_the_time():
    assert HITS_TWO_TO_FIVE == {2: 0.375, 3: 0.375, 4: 0.125, 5: 0.125}
    assert sum(HITS_TWO_TO_FIVE.values()) == 1.0


def test_a_multi_hit_move_beats_one_hit_of_the_same_power():
    # 25 de BP x 3 golpes medios bate 25 de BP uma vez -- e e por isso que o
    # BP nominal de um bullet-seed engana.
    um = probability_of_ko_multi(25, 100, 3, {1: 1.0})
    varios = probability_of_ko_multi(25, 100, 3, HITS_TWO_TO_FIVE)
    assert varios > um


def test_the_hit_count_is_drawn_every_turn_not_once():
    # A contagem sorteia-se de novo em cada turno, logo o total de golpes e
    # uma soma aleatoria: um turno de 2-5 golpes de 20 nao chega aos 150 HP
    # de maneira nenhuma (5 x 20 = 100), dois chegam raramente, tres chegam
    # metade das vezes.
    def ko(turns):
        return probability_of_ko_multi(20, 150, turns, HITS_TWO_TO_FIVE)
    assert ko(1) == 0.0
    assert 0 < ko(2) < ko(3) < 1
