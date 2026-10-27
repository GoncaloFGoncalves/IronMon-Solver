from mon.formula import damage_before_roll


def test_the_reference_case():
    # Caso de referencia da formula de Gen 3: nivel 100, move de 100 BP,
    # atacante e defensor com o stat a 100, sem STAB e sem vantagem de tipo.
    # A formula da 86 de dano antes do roll.
    assert damage_before_roll(level=100, power=100, attack=100, defense=100,
                              stab=False, effectiveness=1) == 86


def test_stab_adds_half_again():
    # Mesmo caso de referencia (86), agora com o move do tipo do atacante.
    assert damage_before_roll(level=100, power=100, attack=100, defense=100,
                              stab=True, effectiveness=1) == 129


def test_type_effectiveness_scales_the_result():
    # A efetividade vem do type chart e multiplica no fim.
    caso = dict(level=100, power=100, attack=100, defense=100, stab=False)
    assert damage_before_roll(**caso, effectiveness=2) == 172
    assert damage_before_roll(**caso, effectiveness=0.5) == 43
    assert damage_before_roll(**caso, effectiveness=4) == 344


def test_an_immune_defender_takes_nothing():
    # Ex: ELECTRIC contra GROUND. Zero nao e "pouco dano" -- e zero.
    assert damage_before_roll(level=100, power=100, attack=100, defense=100,
                              stab=True, effectiveness=0) == 0
