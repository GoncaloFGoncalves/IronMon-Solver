from mon.battle import Combatant
from mon.conditional import TURNS_PER_HIT, focus_punch, turns_per_hit


def test_a_normal_move_hits_every_turn():
    assert turns_per_hit("extrasensory") == 1


def test_a_two_turn_move_costs_a_turn_and_keeps_its_power():
    # O BP nao se desconta: o custo e o turno, e quem o paga e o motor de
    # sequencia. Dividir o BP por 2 apagava o turno de graca do adversario.
    assert turns_per_hit("hyper-beam") == 2
    assert turns_per_hit("solar-beam") == 2
    assert TURNS_PER_HIT["sky-attack"] == 2


def test_focus_punch_always_moves_last():
    me = Combatant(damage=100, hp=120, speed=200)
    them = Combatant(damage=30, hp=100, speed=10)
    assert focus_punch(me, them).speed < them.speed


def test_focus_punch_fails_whenever_the_opponent_damages_me():
    # Prioridade -3 e quebra com qualquer dano: so sai se ele nao agir.
    me = Combatant(damage=100, hp=120, speed=50)
    agil = Combatant(damage=30, hp=100, speed=60)
    assert focus_punch(me, agil).action_chance == 0.0

    paralisado = Combatant(damage=30, hp=100, speed=60, action_chance=0.75)
    assert focus_punch(me, paralisado).action_chance == 0.25
