"""A cadeia de breakpoint: onde cai a linha de morte, por tipo."""

import pytest

from mon.breakpoints import (THREAT_TYPICAL, THREAT_WORST, Threat, Rung,
                             chain, breakpoint_of, chains_by_type)
from mon.damage import probability_of_ko
from mon.veekun import load_moves, load_species
from mon.variants import variants


@pytest.fixture(scope="module")
def moves():
    return [m for m in load_moves() if m.kind == "power" and m.power]


@pytest.fixture(scope="module")
def gyarados():
    species = [s for s in load_species() if s.name == "gyarados"][0]
    return [v for v in variants(species, 70, 27)
            if v.profile == ("physical", "def_tank", "fast")][0]


def test_the_chain_is_sorted_by_damage_descending(gyarados, moves):
    rungs = chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56)
    assert [r.damage for r in rungs] == sorted(
        (r.damage for r in rungs), reverse=True)


def test_every_damaging_move_of_the_type_appears(gyarados, moves):
    rungs = chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56)
    assert len(rungs) == sum(1 for m in moves if m.type == "ELECTRIC")


def test_whether_spark_kills_depends_on_stab_not_on_the_attacking_stat(
        gyarados, moves):
    # A pergunta que motivou a tabela: o thunderbolt mata, mas o spark?
    # A resposta nao e uma so, e e o STAB que a parte -- nao o percentil.
    # De um atacante mediano sem STAB o spark faz 144 contra 161 de HP e
    # nao mata; vindo de um mon ELECTRIC faz 216 e mata sempre.
    sem = {r.move: r for r in
           chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56)}
    com = {r.move: r for r in
           chain(gyarados, moves, "ELECTRIC", Threat(95, 95, 1.5), level=56)}
    assert sem["thunderbolt"].ohko == 1.0 and com["thunderbolt"].ohko == 1.0
    assert sem["spark"].damage == 144 and sem["spark"].ohko == 0.0
    assert com["spark"].damage == 216 and com["spark"].ohko == 1.0


def test_the_breakpoint_is_the_last_rung_that_always_kills(gyarados, moves):
    rungs = chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56)
    last, first = breakpoint_of(rungs)
    assert last.move == "thunderbolt"
    # O degrau seguinte nao e um "nao mata" limpo: e um roll de 12.5%, que e
    # precisamente o caso que a tabela existe para mostrar.
    assert first.move == "thunder-punch"
    assert first.ohko == 0.125
    # E consistente com a propria cadeia: tudo acima mata, ele nao.
    assert all(r.ohko == 1.0 for r in rungs[:rungs.index(last) + 1])
    assert first.ohko < 1.0


def test_a_resisted_type_has_no_breakpoint_at_all(gyarados, moves):
    # def=212 contra ROCK fisico: a cadeia e toda "nao mata", logo nao ha
    # degrau que mate e `last` e None.
    rungs = chain(gyarados, moves, "ROCK", THREAT_TYPICAL, level=56)
    last, first = breakpoint_of(rungs)
    assert last is None
    assert first is rungs[0]
    assert all(r.ohko == 0.0 for r in rungs)


def test_an_immune_type_yields_zero_damage(moves):
    species = [s for s in load_species() if s.name == "gengar"][0]
    ghost = [v for v in variants(species, 70, 27)][0]
    rungs = chain(ghost, moves, "NORMAL", THREAT_TYPICAL, level=56)
    assert all(r.damage == 0 and r.ohko == 0.0 for r in rungs)


def test_the_worst_case_threat_never_kills_less_than_the_typical(gyarados, moves):
    for kind in ("ELECTRIC", "ROCK", "GRASS", "NORMAL"):
        tipico = chain(gyarados, moves, kind, THREAT_TYPICAL, level=56)
        pior = chain(gyarados, moves, kind, THREAT_WORST, level=56)
        for a, b in zip(tipico, pior):
            assert b.damage >= a.damage
            assert b.ohko >= a.ohko


def test_damage_and_ohko_agree_with_the_scalar_kernel(gyarados, moves):
    # Teste diferencial: a cadeia nao pode discordar do `probability_of_ko`,
    # que e o caminho independente ja validado por convolucao.
    for kind in ("ELECTRIC", "ICE", "FIGHTING"):
        for rung in chain(gyarados, moves, kind, THREAT_WORST, level=56):
            assert rung.ohko == probability_of_ko(rung.damage, gyarados.hp, 1)
            assert rung.two == probability_of_ko(rung.damage, gyarados.hp, 2)


def test_every_type_with_a_damaging_move_gets_a_chain(gyarados, moves):
    todas = chains_by_type(gyarados, moves, THREAT_TYPICAL, level=56)
    assert len(todas) == len({m.type for m in moves})
    assert all(todas.values())


def test_the_worst_case_can_leave_no_surviving_rung(gyarados, moves):
    # Com p90 e STAB o movepool ELECTRIC inteiro mata este Gyarados, ate o
    # thunder-shock de 40. Nao ha degrau que falhe -> `first` e None.
    rungs = chain(gyarados, moves, "ELECTRIC", THREAT_WORST, level=56)
    last, first = breakpoint_of(rungs)
    assert first is None
    assert last is rungs[-1] and last.move == "thunder-shock"


def test_a_threat_scales_the_attacking_stat(gyarados, moves):
    forte = Threat(attack=300, special_attack=300, stab=1.5)
    fraco = Threat(attack=10, special_attack=10, stab=1.0)
    a = chain(gyarados, moves, "ELECTRIC", forte, level=56)[0]
    b = chain(gyarados, moves, "ELECTRIC", fraco, level=56)[0]
    assert a.damage > b.damage


def test_threat_levels_scale_with_the_opponent_level():
    from mon.breakpoints import threat_levels
    cedo = threat_levels("brock")
    tarde = threat_levels("elite-4")
    assert tarde.typical.attack > cedo.typical.attack
    assert tarde.worst.attack > tarde.typical.attack


def test_the_typical_threat_has_no_stab_and_the_worst_one_has():
    from mon.breakpoints import threat_levels
    # Os moves sao sorteados do pool inteiro, logo um move ELECTRIC cai quase
    # sempre num mon que nao e ELECTRIC: o caso tipico e sem STAB, e o STAB
    # pertence ao pior caso.
    pair = threat_levels("koga")
    assert pair.typical.stab == 1.0
    assert pair.worst.stab == 1.5


def test_the_koga_threat_matches_the_module_constants():
    from mon.breakpoints import threat_levels, THREAT_TYPICAL, THREAT_WORST
    # As constantes do modulo sao as do Koga (lv56), que e o caso de
    # referencia usado nos testes acima.
    pair = threat_levels("koga")
    assert pair.typical == THREAT_TYPICAL
    assert pair.worst == THREAT_WORST


def test_an_unknown_checkpoint_is_an_error():
    from mon.breakpoints import threat_levels
    with pytest.raises(KeyError):
        threat_levels("viridian-forest")


def test_a_wounded_target_is_asked_about_with_the_hp_override(gyarados, moves):
    # A cadeia e feita a HP cheio por omissao, que e o que engana: a 88 de HP
    # nada ELECTRIC mata este Gyarados na Misty, e a 12 quase tudo mata.
    cheio = chain(gyarados, moves, "PSYCHIC", THREAT_TYPICAL, level=56)
    ferido = chain(gyarados, moves, "PSYCHIC", THREAT_TYPICAL, level=56, hp=12)
    assert all(r.ohko == 0.0 for r in cheio)
    assert sum(1 for r in ferido if r.ohko == 1.0) >= 5
    # O dano nao muda -- o que muda e o denominador.
    assert [r.damage for r in cheio] == [r.damage for r in ferido]


def test_the_hp_override_leaves_the_default_untouched(gyarados, moves):
    sem = chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56)
    com = chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56,
                hp=gyarados.hp)
    assert sem == com


def test_chains_by_type_passes_the_hp_through(gyarados, moves):
    # O que importa e a monotonia: quanto menos HP, mais moves do pool matam.
    # Nesta variante vai de 4 moves em 194 a HP cheio para 103 aos 12 de HP.
    def lethal(hp):
        chains = chains_by_type(gyarados, moves, THREAT_TYPICAL, level=56, hp=hp)
        return sum(1 for rungs in chains.values() for r in rungs if r.ohko == 1.0)

    counts = [lethal(hp) for hp in (gyarados.hp, 40, 20, 12)]
    assert counts == sorted(counts)
    assert counts[0] == 4 and counts[-1] == 103


def test_hp_must_be_positive(gyarados, moves):
    with pytest.raises(ValueError):
        chain(gyarados, moves, "ELECTRIC", THREAT_TYPICAL, level=56, hp=0)
