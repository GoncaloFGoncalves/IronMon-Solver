from mon.dex import Species
from mon.skew import BULKY, FAST, HYBRID, PHYSICAL, SPECIAL
from mon.variants import Variant, attack_damage, variants

SNORLAX = Species(143, "snorlax", ("NORMAL",), 540)


def test_a_species_becomes_twenty_seven_variants():
    todas = variants(SNORLAX, level=50, iv=31)
    assert len(todas) == 27
    assert all(isinstance(v, Variant) for v in todas)


def test_the_bst_is_preserved_across_every_variant():
    # O Kaizo redistribui os stats mas preserva o BST (CONTEXT.md 1.1).
    # Ao nivel 1 com IV 0 a soma dos stats reflecte-o; aqui conferimos que
    # nenhuma variante inventa nem perde poder.
    base_totals = {round(sum(v.bases)) for v in variants(SNORLAX, 50, 31)}
    assert base_totals == {540}


def test_the_physical_variant_hits_harder_than_the_special_one_physically():
    todas = {v.profile: v for v in variants(SNORLAX, 50, 31)}
    fisico = todas[(PHYSICAL, HYBRID, HYBRID)]
    especial = todas[(SPECIAL, HYBRID, HYBRID)]
    assert fisico.attack > especial.attack
    assert fisico.special_attack < especial.special_attack


def test_a_bulky_variant_is_slower_and_tougher():
    todas = {v.profile: v for v in variants(SNORLAX, 50, 31)}
    tanque = todas[(HYBRID, HYBRID, BULKY)]
    veloz = todas[(HYBRID, HYBRID, FAST)]
    assert tanque.hp > veloz.hp and tanque.speed < veloz.speed


def test_a_lower_iv_band_is_strictly_worse():
    forte = variants(SNORLAX, 50, 27)[0]
    fraco = variants(SNORLAX, 50, 5)[0]
    assert fraco.hp < forte.hp and fraco.attack < forte.attack


def test_stab_and_effectiveness_both_land_on_the_damage():
    atacante = variants(SNORLAX, 50, 31)[0]
    defensor = variants(SNORLAX, 50, 31)[0]
    neutro = attack_damage(atacante, defensor, power=80, move_type="WATER")
    com_stab = attack_damage(atacante, defensor, power=80, move_type="NORMAL")
    assert com_stab > neutro

    fantasma = Species(94, "gengar", ("GHOST", "POISON"), 500)
    imune = variants(fantasma, 50, 31)[0]
    assert attack_damage(atacante, imune, power=80, move_type="NORMAL") == 0
