from mon.trainers import (AREA_SPLITS, LEADERS, SPLITS, Trainer,
                          parse_trainers, trainers_before)

AMOSTRA = """
  // Viridian Forest
  {
    name: "Bug Catcher Rick",
    numPokemon: 2,
    pokemonLevels: [9, 9],
  },
  // Pewter Gym
  {
    name: "Camper Liam",
    numPokemon: 2,
    pokemonLevels: [15, 17],
  },
  {
    name: "Brock",
    numPokemon: 5,
    pokemonLevels: [18, 18, 18, 18, 21],
  },
  // Mt. Moon
  // B2F
  {
    name: "Super Nerd Miguel",
    numPokemon: 3,
    pokemonLevels: [17, 17, 17],
  },
"""


def test_a_trainer_carries_its_area_and_its_party():
    parsed = parse_trainers(AMOSTRA)
    assert parsed[0] == Trainer("Viridian Forest", "Bug Catcher Rick", (9, 9))


def test_a_floor_comment_does_not_start_a_new_area():
    # "B2F" e um piso da Mt. Moon, nao uma area.
    parsed = parse_trainers(AMOSTRA)
    assert parsed[-1].area == "Mt. Moon"


def test_every_area_in_the_data_belongs_to_a_split():
    from mon.trainers import load_trainers
    areas = {t.area for t in load_trainers()}
    assert areas - set(AREA_SPLITS) == set()


def test_the_splits_are_the_nine_checkpoints_in_route_order():
    assert SPLITS == ("brock", "misty", "surge", "erika", "koga",
                      "sabrina", "blaine", "giovanni", "elite-4")


def test_the_leader_does_not_pay_for_reaching_himself():
    # O EXP do Brock conta para o split seguinte, nao para chegar ao Brock.
    parsed = parse_trainers(AMOSTRA)
    antes = trainers_before("brock", parsed)
    assert "Brock" in LEADERS
    assert [t.name for t in antes] == ["Bug Catcher Rick", "Camper Liam"]


def test_a_later_split_includes_everything_before_it():
    from mon.trainers import load_trainers
    todos = load_trainers()
    for mais_cedo, mais_tarde in zip(SPLITS, SPLITS[1:]):
        assert (len(trainers_before(mais_cedo, todos))
                < len(trainers_before(mais_tarde, todos)))


def test_moving_trainers_are_flagged():
    from mon.trainers import load_trainers, unavoidable
    todos = load_trainers()
    moveis = [t for t in todos if t.spinner or t.walker]
    assert len(moveis) == 100, "59 spinners + 41 walkers no mapa"
    # Os que se mexem nao se contornam de forma fiavel; os lideres e o rival
    # sao obrigatorios por serem o proprio caminho.
    forcados = unavoidable(todos)
    assert len(moveis) < len(forcados) < len(todos)
    assert any(t.name == "Brock" for t in forcados)


def test_the_splits_are_the_same_checkpoints_the_rest_of_the_code_uses():
    # Tres modulos com tres grafias dos mesmos 9 checkpoints e um bug a
    # espera. O `checkpoints.py` e a fonte; este teste falha se divergirem.
    from mon.checkpoints import CHECKPOINTS
    from mon.trainers import slug
    assert tuple(slug(cp.name) for cp in CHECKPOINTS) == SPLITS
