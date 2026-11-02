from mon.dungeons import DUNGEONS, mandatory_battles


def test_the_gym_counts_agree_with_the_trainer_data():
    # O `dungeons.py` e escrito a mao; o `gauntlet.py` le o mapa. Se
    # divergirem, um dos dois esta errado -- e o teste diz qual.
    from mon.gauntlet import stages_of
    from mon.trainers import load_trainers
    secoes = {"brock": "pewter-gym", "misty": "cerulean-gym",
              "surge": "vermilion-gym", "erika": "celadon-gym",
              "koga": "fuchsia-gym", "sabrina": "saffron-gym",
              "blaine": "cinnabar-gym", "giovanni": "viridian-gym"}
    trainers = load_trainers()
    for checkpoint, section in secoes.items():
        assert mandatory_battles(section) == len(stages_of(checkpoint, trainers))


def test_the_five_big_sections_are_covered():
    nomes = {d.name for d in DUNGEONS}
    assert {"ss-anne", "rocket-hideout", "pokemon-tower", "silph-co"} <= nomes


def test_a_gym_counts_every_trainer_in_the_room():
    # Regra do desafio: os treinadores de ginasio sao todos obrigatorios.
    # Pewter sao 2 embates (o Camper Liam e o Brock), nao 1.
    assert mandatory_battles("pewter-gym") == 2
    assert mandatory_battles("celadon-gym") == 8


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
