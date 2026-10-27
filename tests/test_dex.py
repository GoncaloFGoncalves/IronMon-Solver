from mon.dex import GEN_3, build_species

TYPES = [{"id": "1", "identifier": "normal"}, {"id": "4", "identifier": "poison"}]


def test_builds_a_species_from_csv_rows():
    # Snorlax: numero 143, tipo unico NORMAL, stats 160/110/65/65/110/30.
    species = build_species(
        pokemon=[{"id": "143", "identifier": "snorlax"}],
        pokemon_types=[{"pokemon_id": "143", "type_id": "1", "slot": "1"}],
        pokemon_stats=[{"pokemon_id": "143", "stat_id": str(i), "base_stat": s}
                       for i, s in enumerate(["160", "110", "65", "65", "110", "30"], 1)],
        types=TYPES,
    )
    assert len(species) == 1
    assert species[0].number == 143
    assert species[0].name == "snorlax"
    assert species[0].types == ("NORMAL",)
    assert species[0].bst == 540


def test_dual_types_come_out_in_slot_order():
    # Bulbasaur e GRASS/POISON, nesta ordem. As linhas vem propositadamente
    # trocadas: a ordem tem de vir do slot, nao da ordem do ficheiro.
    # Importa porque (tipos, BST) e chave de tabela (CONTEXT.md 1.2).
    species = build_species(
        pokemon=[{"id": "1", "identifier": "bulbasaur"}],
        pokemon_types=[{"pokemon_id": "1", "type_id": "4", "slot": "2"},
                       {"pokemon_id": "1", "type_id": "12", "slot": "1"}],
        pokemon_stats=[{"pokemon_id": "1", "stat_id": "1", "base_stat": "318"}],
        types=[{"id": "12", "identifier": "grass"}, {"id": "4", "identifier": "poison"}],
    )
    assert species[0].types == ("GRASS", "POISON")


def test_filters_to_the_requested_numbers():
    # O pokemon.csv do veekun traz formas alternativas com id acima de 10000
    # (deoxys-attack e afins). O pool sao os 386 de Gen 3 (CONTEXT.md 3.1).
    rows = [{"id": "386", "identifier": "deoxys-normal"},
            {"id": "10001", "identifier": "deoxys-attack"}]
    stats = [{"pokemon_id": i, "stat_id": "1", "base_stat": "600"}
             for i in ("386", "10001")]
    types = [{"pokemon_id": i, "type_id": "14", "slot": "1"} for i in ("386", "10001")]

    species = build_species(rows, types, stats,
                            [{"id": "14", "identifier": "psychic"}],
                            numbers=GEN_3)
    assert [s.name for s in species] == ["deoxys-normal"]
