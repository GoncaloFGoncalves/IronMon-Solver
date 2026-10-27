from mon.dungeons import DUNGEONS, mandatory_battles


def test_the_five_big_sections_are_covered():
    nomes = {d.name for d in DUNGEONS}
    assert {"ss-anne", "rocket-hideout", "pokemon-tower", "silph-co"} <= nomes


def test_a_gym_counts_the_leader_and_nothing_optional():
    assert mandatory_battles("pewter-gym") == 1


def test_only_the_mandatory_path_counts():
    # O resto dos treinadores e opcional: o trade-off e chegar mais fraco.
    assert mandatory_battles("ss-anne") == 1
    assert mandatory_battles("pokemon-tower") > mandatory_battles("ss-anne")


def test_an_unknown_section_is_not_silently_zero():
    try:
        mandatory_battles("mt-moon")
    except KeyError:
        return
    raise AssertionError("uma secao desconhecida tem de falhar, nao dar 0")
