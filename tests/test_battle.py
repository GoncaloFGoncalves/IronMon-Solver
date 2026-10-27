from mon.battle import Combatant, moves_first, win_probability


def test_the_faster_mon_attacks_first():
    # Com dois mons no perfil hibrido, Speed = BST/6, logo quem tem mais BST
    # ataca primeiro: Snorlax (540) contra Weepinbell (390).
    assert moves_first(speed=90, opposing_speed=65) == 1.0
    assert moves_first(speed=65, opposing_speed=90) == 0.0


def test_a_speed_tie_is_a_coin_flip():
    assert moves_first(speed=90, opposing_speed=90) == 0.5


def test_faster_and_one_shots_always_wins():
    eu = Combatant(damage=1000, hp=100, speed=100)
    ele = Combatant(damage=1000, hp=100, speed=50)
    assert win_probability(eu, ele) == 1.0


def test_slower_and_gets_one_shot_always_loses():
    eu = Combatant(damage=1000, hp=100, speed=50)
    ele = Combatant(damage=1000, hp=100, speed=100)
    assert win_probability(eu, ele) == 0.0


def test_between_equals_the_speed_decides():
    # Dois mons identicos, ambos garantidos a derrubar em 2 golpes e nenhum
    # em 1. Quem ataca primeiro chega la primeiro -- e isto que torna a
    # paralisia valiosa num mon lento (CONTEXT.md 3.6).
    rapido = Combatant(damage=60, hp=100, speed=90)
    lento = Combatant(damage=60, hp=100, speed=50)
    assert win_probability(rapido, lento) == 1.0
    assert win_probability(lento, rapido) == 0.0


def test_a_genuinely_uncertain_trade():
    # Ambos com dano medio de 53% do HP: P(2HKO) = 25% cada um.
    # Sou o mais lento, logo so ganho se o derrubar em 2 golpes E ele falhar
    # o dele: 0.25 x 0.75 = 0.1875.
    eu = Combatant(damage=53, hp=100, speed=50)
    ele = Combatant(damage=53, hp=100, speed=90)
    assert round(win_probability(eu, ele), 3) == 0.188


def test_the_value_of_an_effect_depends_on_who_has_it():
    # A razao de ser deste motor: o upside e o swing na troca, e o mesmo
    # efeito vale coisas diferentes conforme o perfil (CONTEXT.md 3.5b).
    # A paralisia em Gen 3 corta a Speed a 1/4.
    ele = Combatant(damage=53, hp=100, speed=90)
    paralisado = Combatant(damage=53, hp=100, speed=90 * 0.25)

    lento = Combatant(damage=53, hp=100, speed=50)
    swing_no_lento = win_probability(lento, paralisado) - win_probability(lento, ele)

    rapido = Combatant(damage=53, hp=100, speed=150)
    swing_no_rapido = win_probability(rapido, paralisado) - win_probability(rapido, ele)

    assert round(swing_no_lento, 3) == 0.625
    assert swing_no_rapido == 0.0


def test_a_lost_turn_can_hand_over_the_trade():
    # Ambos derrubam de um golpe e eu sou o mais lento: normalmente perco
    # sempre. Se ele so agir em metade dos turnos, metade das vezes nao chega
    # a atacar e eu ganho. E assim que a paralisia e o flinch viram trocas.
    eu = Combatant(damage=1000, hp=100, speed=50)
    ele = Combatant(damage=1000, hp=100, speed=100, action_chance=0.5)
    assert win_probability(eu, ele) == 0.5


def test_residual_damage_alone_can_win_the_trade():
    # Nenhum dos dois causa dano de golpe. Ele perde 100 de HP por turno a
    # status (burn, poison, leech seed) e cai sozinho ao fim do primeiro.
    eu = Combatant(damage=0, hp=100, speed=100)
    ele = Combatant(damage=0, hp=100, speed=50, residual=100)
    assert win_probability(eu, ele) == 1.0


def test_residual_brings_the_ko_forward():
    # Com 25 de dano nao chego a derrubar 100 de HP em 4 turnos: os 4 golpes
    # somam 100 so com rolls maximos. Um burn de 12 por turno tira 36 pelo
    # caminho e a conta passa a fechar sempre.
    eu = Combatant(damage=25, hp=100, speed=100)
    limpo = Combatant(damage=0, hp=100, speed=1)
    queimado = Combatant(damage=0, hp=100, speed=1, residual=12)
    assert win_probability(eu, limpo) < 0.01
    assert win_probability(eu, queimado) == 1.0
