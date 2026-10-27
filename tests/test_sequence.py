from mon.sequence import Fighter, State, resolve, run_section


def oponente(damage=30, hp=100, speed=50):
    return Fighter(damage=damage, hp=hp, speed=speed)


def test_a_battle_leaves_a_distribution_of_states_not_a_number():
    me = Fighter(damage=60, hp=120, speed=60, pp=20)
    out = resolve(me, oponente())
    assert 0 < out.survival <= 1
    assert abs(sum(out.states.values()) - out.survival) < 1e-9


def test_pp_is_spent_and_carries_to_the_next_battle():
    me = Fighter(damage=200, hp=120, speed=60, pp=20)   # OHKO garantido
    out = resolve(me, oponente())
    assert all(s.pp == 19 for s in out.states), "um OHKO gasta exatamente 1 PP"


def test_recoil_follows_the_mon_into_the_next_battle():
    # O exemplo do double-edge: mata ao primeiro turno e entra no mon
    # seguinte com menos HP, porque o recuo nao se cura dentro da dungeon.
    me = Fighter(damage=200, hp=120, speed=60, recoil=1 / 3)
    out = resolve(me, oponente())
    assert all(s.hp < 120 for s in out.states)
    assert all(s.hp > 120 - 200 / 3 - 1 for s in out.states)


def test_a_pending_dead_turn_follows_the_mon_into_the_next_battle():
    # O mon que mata com um move de dois turnos entra no embate seguinte a
    # deverr um turno -- o mesmo que o Truant.
    me = Fighter(damage=200, hp=120, speed=60, turns_per_hit=2)
    out = resolve(me, oponente())
    assert all(s.owed == 1 for s in out.states)


def hp_medio(out):
    return sum(s.hp * p for s, p in out.states.items()) / out.survival


def test_a_dead_turn_is_a_free_turn_for_the_opponent():
    # O custo do turno morto e o adversario atacar de graca -- mede-se no HP
    # com que fico, nao no dano que dou. Mesmo dano, mesma troca ganha, 41 HP
    # a menos: e isto que um BP/turno apagava.
    them = oponente(damage=45, hp=200)
    sem = resolve(Fighter(damage=150, hp=140, speed=60), them)
    com = resolve(Fighter(damage=150, hp=140, speed=60, turns_per_hit=2), them)
    assert hp_medio(com) < hp_medio(sem) - 30


def test_a_two_turn_move_is_not_the_same_as_half_the_power_every_turn():
    # 150 BP a cada dois turnos nao e 75 BP por turno. Aqui e melhor, porque
    # o dobro do BP corta um golpe ao numero de golpes necessarios -- o turno
    # morto so custa quando nao corta nenhum.
    them = oponente(damage=50, hp=200)
    meio = resolve(Fighter(damage=75, hp=120, speed=60), them)
    inteiro = resolve(Fighter(damage=150, hp=120, speed=60, turns_per_hit=2), them)
    assert inteiro.survival != meio.survival


def test_a_section_chains_the_opponents_through_the_same_state():
    # Tres vezes o mesmo mon nao e tres vezes a mesma troca: o HP e o PP
    # nao se repoem, e por isso o terceiro embate comeca em desvantagem.
    me = Fighter(damage=90, hp=200, speed=60, pp=10)
    them = oponente(damage=70, hp=150)
    assert resolve(me, them).survival == 1.0
    out = run_section(me, [them] * 3)
    assert out.survival < 1.0
    assert all(s.pp <= 10 - 3 for s in out.states), "tres mons custam >=3 PP"


def test_running_out_of_pp_inside_a_section_is_death():
    me = Fighter(damage=90, hp=500, speed=60, pp=2)
    out = run_section(me, [oponente()] * 5)
    assert out.survival == 0.0


def test_drain_heals_but_never_above_the_maximum():
    me = Fighter(damage=60, hp=120, speed=60, drain=0.5)
    out = resolve(me, oponente(damage=1))
    assert all(s.hp <= 120 for s in out.states)


def test_a_state_can_be_handed_to_the_next_battle():
    me = Fighter(damage=200, hp=120, speed=60, pp=20)
    meio = State(hp=60, pp=5, owed=0)
    out = resolve(me, oponente(), meio)
    assert all(s.pp == 4 for s in out.states)
    assert all(s.hp <= 60 for s in out.states)
