from mon.abilities import (
    DUNGEON_SELF_STATUS,
    GUTS_WINDOW_TURNS,
    MonContext,
    swing,
    utilization,
)
from mon.battle import Combatant


def contexto(physical=True, recoil=False, incoming_physical=True):
    # Troca a serio: eu mais tanky e mais lento, ele bate mais forte.
    # A 0.417 de base ha espaco para a habilidade mexer nos dois sentidos --
    # num matchup ja decidido nenhuma habilidade vale nada.
    return MonContext(
        me=Combatant(damage=36, hp=120, speed=40),
        them=Combatant(damage=42, hp=100, speed=60),
        physical=physical,
        recoil=recoil,
        incoming_physical=incoming_physical,
    )


def test_ability_without_modelled_mechanics_is_worth_nothing():
    # Opcao (c): so as habilidades com mecanica modelada valem swing.
    assert utilization("illuminate", contexto()) == 0.0


def test_truant_is_the_worst_outcome_possible():
    # Metade dos turnos perdidos: o swing e negativo e grande.
    assert swing("truant", contexto()) < -0.25


def test_guts_pays_for_itself_with_the_status_it_needs():
    # 1.5x de Atk, menos 1/8 do HP por turno. O ganho liquido e pequeno, e
    # num mon fragil chega a ser negativo -- o status nao e gratis.
    ctx = contexto()
    assert 0 < swing("guts", ctx) < 0.15


def test_guts_only_helps_a_physical_moveset():
    assert swing("guts", contexto(physical=True)) > 0
    assert swing("guts", contexto(physical=False)) == 0.0


def test_dungeon_rules_cut_the_value_of_guts():
    # Nao se pode auto-infligir status numa dungeon (nem cura, nem mons
    # selvagens), logo o swing bruto do Guts e inaproveitavel na maior parte.
    ctx = contexto(physical=True)
    assert 0 < utilization("guts", ctx) < swing("guts", ctx)
    assert DUNGEON_SELF_STATUS < 1.0


def test_the_guts_window_is_eight_turns():
    # Burn e poison tiram 1/8 do HP por turno em Gen 3: ao oitavo turno o mon
    # morre, e sem cura dentro da dungeon nao ha prolongamento.
    assert GUTS_WINDOW_TURNS == 8


def test_intimidate_is_unconditional_against_a_physical_attacker():
    ctx = contexto(incoming_physical=True)
    assert utilization("intimidate", ctx) == swing("intimidate", ctx) > 0
    assert swing("intimidate", contexto(incoming_physical=False)) == 0.0


def test_rock_head_is_worth_nothing_without_a_recoil_move():
    assert swing("rock-head", contexto(recoil=False)) == 0.0
    assert swing("rock-head", contexto(recoil=True)) > 0
