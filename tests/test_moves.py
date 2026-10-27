from mon.damage import HITS_TWO_TO_FIVE
from mon.moves import build_moves

TYPES = [{"id": "1", "identifier": "normal"}, {"id": "10", "identifier": "fire"}]


def linha(identifier, type_id, power, damage_class_id="3"):
    return {"identifier": identifier, "type_id": type_id, "power": power,
            "damage_class_id": damage_class_id}


def test_category_comes_from_the_type_not_from_damage_class():
    # Em Gen 3 o split fisico/especial e por TIPO, nao por move. O campo
    # damage_class do veekun e a classificacao Gen 4+: usa-la da a resposta
    # errada para FRLG (CONTEXT.md 3.1, lacuna 2).
    # Hyper Beam e NORMAL -> fisico em Gen 3, apesar de o veekun dizer special.
    moves = build_moves([linha("hyper-beam", "1", "150")], TYPES)
    assert moves[0].is_physical is True


def test_excluded_moves_never_come_out():
    # GRUPOS.md: fora os OHKO (A1), os setup (A2), os que matam o proprio
    # (B3) e os de dano condicional descartados (B1, B1b).
    rows = [linha(n, "1", "100") for n in
            ("fissure", "swords-dance", "explosion", "self-destruct",
             "counter", "mirror-coat", "reversal", "flail", "bide",
             "endeavor", "spit-up", "beat-up", "present", "psywave")]
    rows.append(linha("body-slam", "1", "85"))
    assert [m.name for m in build_moves(rows, TYPES)] == ["body-slam"]


def test_effective_bp_overrides():
    # GRUPOS.md B1: moves cujo BP nao esta na tabela e foi calculado.
    rows = [linha("low-kick", "1", ""), linha("magnitude", "1", ""),
            linha("return", "1", ""), linha("frustration", "1", "")]
    bp = {m.name: m.power for m in build_moves(rows, TYPES)}
    assert bp["low-kick"] == 56       # media do peso sobre os 386 mons
    assert bp["magnitude"] == 71      # valor esperado das 7 magnitudes
    assert bp["return"] == 102        # amizade maxima
    assert bp["frustration"] == 40    # assumido apos sair do lab


def test_moves_whose_damage_is_not_bp_based():
    # GRUPOS.md B1/B1b: quatro maneiras de causar dano alem do BP.
    rows = [linha(n, "1", "") for n in
            ("seismic-toss", "night-shade", "dragon-rage", "sonic-boom",
             "super-fang", "toxic")]
    kind = {m.name: (m.kind, m.power) for m in build_moves(rows, TYPES)}
    assert kind["seismic-toss"] == ("level", 0)   # dano = nivel do atacante
    assert kind["night-shade"] == ("level", 0)
    assert kind["dragon-rage"] == ("fixed", 40)   # cai ao longo da run
    assert kind["sonic-boom"] == ("fixed", 20)
    assert kind["super-fang"] == ("fraction", 50)  # metade do HP atual
    assert kind["toxic"] == ("status", 0)


def test_a_normal_move_is_bp_based():
    assert build_moves([linha("body-slam", "1", "85")], TYPES)[0].kind == "power"


def test_only_damaging_status_moves_survive():
    # GRUPOS.md B2/B2b: os status puros ficam fora, mas os que causam dano
    # entram, porque resolvem movesets sem resposta contra certos mons.
    rows = [linha(n, "1", "") for n in
            ("growl", "protect", "recover", "sleep-powder",   # puros, fora
             "toxic", "will-o-wisp", "leech-seed", "spikes")]  # com dano, dentro
    assert sorted(m.name for m in build_moves(rows, TYPES)) == [
        "leech-seed", "spikes", "toxic", "will-o-wisp"]


def test_gen_3_values_not_the_current_ones():
    # ARMADILHA: o moves.csv do veekun tem os valores ATUAIS. 90 dos 354 moves
    # de Gen 3 mudaram depois. O changelog guarda o valor anterior a cada
    # mudanca, e o de Gen 3 e o da mudanca mais antiga posterior a Gen 3.
    rows = [{"identifier": "giga-drain", "type_id": "12", "power": "75", "pp": "10"},
            {"identifier": "extrasensory", "type_id": "14", "power": "80", "pp": "20"}]
    # (geracao em que mudou, campos com o valor de ANTES)
    changelog = {"giga-drain": [(4, {"pp": "5"}), (5, {"power": "60"})],
                 "extrasensory": [(6, {"pp": "30"})]}
    por_nome = {m.name: m for m in build_moves(rows, TYPES + [{"id": "12", "identifier": "grass"},
                                                              {"id": "14", "identifier": "psychic"}],
                                               changelog=changelog)}
    assert (por_nome["giga-drain"].power, por_nome["giga-drain"].pp) == (60, 5)
    assert (por_nome["extrasensory"].power, por_nome["extrasensory"].pp) == (80, 30)


def test_drain_moves_carry_how_much_they_heal():
    # Dentro de uma dungeon nao ha cura. Os moves de dreno sao a unica
    # recuperacao, e por isso o dreno tem de estar nos dados do move.
    rows = [{"identifier": "giga-drain", "type_id": "12", "power": "60", "pp": "5"},
            {"identifier": "razor-leaf", "type_id": "12", "power": "55", "pp": "25"}]
    types = TYPES + [{"id": "12", "identifier": "grass"}]
    meta = {"giga-drain": 50}
    por_nome = {m.name: m for m in build_moves(rows, types, drain=meta)}
    assert por_nome["giga-drain"].drain == 50
    assert por_nome["razor-leaf"].drain == 0


def test_hidden_power_is_out_of_the_pool():
    # O BP depende de IVs que nao se leem antes da run, e o veekun guarda 1
    # como placeholder. Um BP fixo seria inventado.
    from mon.moves import EXCLUDED
    assert "hidden-power" in EXCLUDED


def test_a_multi_hit_move_carries_its_hit_count():
    # Um double-kick bate duas vezes por turno e um bullet-seed 2 a 5. Sem
    # isto o BP nominal engana nos dois sentidos.
    built = build_moves(
        moves=[{"id": "24", "identifier": "double-kick", "type_id": "2",
                "power": "30", "pp": "30"},
               {"id": "31", "identifier": "fury-attack", "type_id": "1",
                "power": "15", "pp": "20"},
               {"id": "33", "identifier": "tackle", "type_id": "1",
                "power": "35", "pp": "35"}],
        types=[{"id": "1", "identifier": "normal"},
               {"id": "2", "identifier": "fighting"}],
        hits={"double-kick": (2, 2), "fury-attack": (2, 5)})
    by_name = {m.name: m for m in built}
    assert by_name["double-kick"].hit_chances == {2: 1.0}
    assert by_name["fury-attack"].hit_chances == HITS_TWO_TO_FIVE
    assert by_name["tackle"].hit_chances == {1: 1.0}


def test_triple_kick_escalates_instead_of_repeating():
    # Em Gen 3 os tres golpes sao 10, 20 e 30 de BP -- 60 no total, nao 30.
    # O veekun guarda 10, que e so o primeiro golpe.
    built = build_moves(
        moves=[{"id": "167", "identifier": "triple-kick", "type_id": "2",
                "power": "10", "pp": "10"}],
        types=[{"id": "2", "identifier": "fighting"}],
        hits={"triple-kick": (3, 3)})
    move = built[0]
    assert move.power * 3 == 60
