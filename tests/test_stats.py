from mon.stats import stat_at_level


def test_non_hp_stat_at_level_100_with_perfect_ivs():
    # Shuckle, base Def 230. Ao nivel 100 com IV 31, sem EVs e nature neutra,
    # a Defense do Shuckle e 496.
    assert stat_at_level(base=230, level=100, iv=31, is_hp=False) == 496


def test_hp_uses_a_different_formula():
    # Blissey, base HP 255. Ao nivel 100 com IV 31 e sem EVs, o HP e 651.
    assert stat_at_level(base=255, level=100, iv=31, is_hp=True) == 651


def test_scales_with_level():
    # Base 100 ao nivel 50 com IV 31 e sem EVs: 120 nos stats normais, 175 no HP.
    # Guarda a posicao do floor: arredonda antes do +5, nao depois.
    assert stat_at_level(base=100, level=50, iv=31, is_hp=False) == 120
    assert stat_at_level(base=100, level=50, iv=31, is_hp=True) == 175


def test_a_fractional_base_stat_is_rounded_to_an_integer():
    # O modelo de skew da base stats fracionarios (BST/6 e afins) para
    # preservar o BST. No jogo um base stat e sempre inteiro, e esta e a
    # fronteira onde se converte (CONTEXT.md 2.0).
    fracionario = stat_at_level(base=500 / 6, level=43, iv=31, is_hp=False)
    assert fracionario == stat_at_level(base=83, level=43, iv=31, is_hp=False)
    assert isinstance(fracionario, int)
