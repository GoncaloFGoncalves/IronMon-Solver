from mon.damage import probability_of_ko


def test_a_hit_averaging_exactly_the_hp_kills_only_on_a_max_roll():
    # O dano em Gen 3 tem 16 rolls inteiros de 85 a 100. Se o dano medio for
    # exatamente o HP, so o roll 100 chega -> 1 em 16.
    assert probability_of_ko(base_damage=100, hp=100, hits=1) == 1 / 16


def test_two_hits_averaging_half_the_hp_almost_never_kill():
    # O caso que mostra porque o valor esperado nao serve: dano medio de 50%
    # do HP parece um 2HKO limpo, mas so os dois rolls maximos chegam a 100%
    # -> 1/256. O valor esperado diria "mata em 2" com confianca.
    assert probability_of_ko(base_damage=50, hp=100, hits=2) == 1 / 256


def test_exact_threshold_counts_as_a_kill():
    # Guarda do bug de arredondamento: com hp 85 e dano medio 100, o roll
    # minimo (85) da exatamente 85 de dano. Tem de contar como KO -> 16/16.
    assert probability_of_ko(base_damage=100, hp=85, hits=1) == 1.0


def test_certainty_at_both_ends():
    assert probability_of_ko(base_damage=1000, hp=100, hits=1) == 1.0
    assert probability_of_ko(base_damage=1, hp=100, hits=2) == 0.0
    assert probability_of_ko(base_damage=0, hp=100, hits=4) == 0.0


def test_matches_the_worked_examples_from_the_spec():
    # Valores do levantamento que fixou a decisao do CONTEXT.md 3.6.
    assert round(probability_of_ko(53, 100, hits=2), 3) == 0.250
    assert round(probability_of_ko(55, 100, hits=2), 3) == 0.625


def test_each_hit_is_floored_on_its_own():
    # Em Gen 3 o dano de cada golpe e truncado sozinho: 3 golpes de base 36
    # dao 30..36 cada, nunca 36 * (soma dos rolls) / 100. Valor verificado
    # por convolucao independente dos danos truncados.
    assert abs(probability_of_ko(36, 100, 3) - 0.366943) < 1e-6


def test_summing_rolls_before_flooring_overstates_the_ko():
    # Regressao do bug: somar os rolls e aplicar o dano uma vez dava 0.5 aqui,
    # 13 pp acima do valor real, e isso propagava-se ao win_probability.
    assert probability_of_ko(36, 100, 3) < 0.4
