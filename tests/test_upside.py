from mon.battle import Combatant
from mon.upside import Upside, scenarios, value


def troca(speed=40):
    return (Combatant(damage=36, hp=120, speed=speed),
            Combatant(damage=42, hp=100, speed=50))


def test_a_move_without_a_secondary_effect_has_no_upside():
    me, them = troca()
    nunca, sempre, real = scenarios(me, them, Upside())
    assert nunca == sempre == real


def test_the_three_scenarios_bracket_the_real_one():
    # O real fica entre "nunca dispara" e "dispara sempre" (CONTEXT.md 3.5b).
    me, them = troca()
    nunca, sempre, real = scenarios(me, them, Upside("paralysis", 0.10))
    assert nunca < real < sempre


def test_the_chance_moves_the_real_scenario_not_the_bounds():
    me, them = troca()
    fraco = scenarios(me, them, Upside("paralysis", 0.10))
    forte = scenarios(me, them, Upside("paralysis", 0.30))
    assert fraco[0] == forte[0] and fraco[1] == forte[1]
    assert fraco[2] < forte[2]


def test_the_same_effect_is_worth_more_to_a_slow_mon():
    # A razao de ser disto: o upside depende do mon, nao do move.
    lento, them = troca(speed=40)
    rapido, _ = troca(speed=90)
    thunderbolt = Upside("paralysis", 0.10)
    assert value(lento, them, thunderbolt) - value(lento, them, Upside()) > \
           value(rapido, them, thunderbolt) - value(rapido, them, Upside())


def test_flinch_only_works_if_i_move_first():
    # Um flinch de quem ataca em segundo nao tira turno nenhum.
    lento, them = troca(speed=40)
    rapido, _ = troca(speed=90)
    headbutt = Upside(flinch=0.30)
    assert scenarios(rapido, them, headbutt)[1] > scenarios(rapido, them, Upside())[1]
    assert scenarios(lento, them, headbutt)[1] == scenarios(lento, them, Upside())[1]


def test_burn_only_cuts_attack_against_a_physical_attacker():
    me, them = troca()
    fisico = scenarios(me, them, Upside("burn", 0.10), physical=True)
    especial = scenarios(me, them, Upside("burn", 0.10), physical=False)
    assert fisico[1] >= especial[1]


def test_more_turns_mean_more_chances_to_trigger():
    me, them = troca()
    curto = scenarios(me, them, Upside("paralysis", 0.10), turns=2)
    longo = scenarios(me, them, Upside("paralysis", 0.10), turns=5)
    assert longo[2] > curto[2]
