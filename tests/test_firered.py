from mon.firered import parse_species_info

AMOSTRA = """
    [SPECIES_BULBASAUR] =
    {
        .baseHP = 45,
        .expYield = 64,
        .growthRate = GROWTH_MEDIUM_SLOW,
    },
    [SPECIES_CATERPIE] =
    {
        .baseHP = 45,
        .expYield = 53,
        .growthRate = GROWTH_MEDIUM_FAST,
    },
"""


def test_the_exp_yield_and_curve_come_from_the_disassembly():
    # O `base_experience` do veekun e moderno: 375 das 386 especies diferem,
    # com os valores atuais a rondar o dobro. A disassembly do FireRed e a
    # fonte autoritativa para Gen 3.
    info = parse_species_info(AMOSTRA)
    assert info["bulbasaur"] == (64, "MEDIUM_SLOW")
    assert info["caterpie"] == (53, "MEDIUM_FAST")
