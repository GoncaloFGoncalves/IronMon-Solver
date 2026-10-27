import pytest

from mon.typechart import GEN_2_TO_5, GEN_2_TO_5_INTERACTIONS, TYPES_GEN_2_TO_5


def test_multiplies_across_both_defending_types():
    # Ice vs Dragon/Flying (ex: Dragonite) e 2x por cada tipo = 4x.
    assert GEN_2_TO_5.effectiveness("ICE", ("DRAGON", "FLYING")) == 4


def test_steel_resists_dark_and_ghost_in_gen_2_to_5():
    # Diferenca face ao chart moderno: so a partir da Gen 6 e que STEEL
    # deixou de resistir a DARK e GHOST. O legado tem isto errado.
    assert GEN_2_TO_5.effectiveness("DARK", ("STEEL",)) == 0.5
    assert GEN_2_TO_5.effectiveness("GHOST", ("STEEL",)) == 0.5


def test_fairy_does_not_exist_in_gen_2_to_5():
    assert "FAIRY" not in TYPES_GEN_2_TO_5
    with pytest.raises(KeyError):
        GEN_2_TO_5.effectiveness("FAIRY", ("DRAGON",))


def test_immunity_beats_everything_else():
    # Ground vs Flying/Ground: 0x por Flying, 2x por Ground -> 0x.
    assert GEN_2_TO_5.effectiveness("GROUND", ("FLYING", "GROUND")) == 0


def test_chart_is_complete_and_closed():
    # Guarda contra gralhas na tabela escrita a mao: todos os 17 tipos tem
    # linha, e nenhuma linha refere um tipo de fora dos 17.
    assert set(GEN_2_TO_5_INTERACTIONS) == set(TYPES_GEN_2_TO_5)
    for attacking, row in GEN_2_TO_5_INTERACTIONS.items():
        unknown = set(row) - set(TYPES_GEN_2_TO_5)
        assert not unknown, f"{attacking} refere tipos desconhecidos: {unknown}"
