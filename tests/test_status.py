from mon.battle import Combatant, win_probability
from mon.status import burned, paralysed, poisoned


def test_paralysis_quarters_speed_and_costs_a_quarter_of_the_turns():
    # Gen 3: a paralisia corta a Speed a 1/4 e falha 25% dos turnos.
    alvo = paralysed(Combatant(damage=100, hp=200, speed=120))
    assert alvo.speed == 30
    assert alvo.action_chance == 0.75


def test_burn_halves_physical_damage_and_bleeds_an_eighth_of_hp():
    # Gen 3: o burn corta o Atk a metade (so fisico) e tira 1/8 do HP maximo.
    fisico = burned(Combatant(damage=100, hp=200, speed=50), physical=True)
    assert fisico.damage == 50
    assert fisico.residual == 25

    especial = burned(Combatant(damage=100, hp=200, speed=50), physical=False)
    assert especial.damage == 100
    assert especial.residual == 25


def test_poison_only_bleeds():
    envenenado = poisoned(Combatant(damage=100, hp=200, speed=50))
    assert envenenado.damage == 100
    assert envenenado.residual == 25


def test_the_same_effect_is_worth_less_to_a_faster_mon():
    # Razao de ser do modelo de upside (CONTEXT.md 3.5b): o valor de um efeito
    # esta no perfil de quem o usa, nao no efeito. A paralisia vale muito a um
    # mon lento e pouco a um rapido -- e nenhuma tabela por move apanha isso.
    ele = Combatant(damage=53, hp=100, speed=90)
    def swing(speed):
        eu = Combatant(damage=53, hp=100, speed=speed)
        return win_probability(eu, paralysed(ele)) - win_probability(eu, ele)
    assert round(swing(50), 3) == 0.707
    assert round(swing(150), 3) == 0.082
    assert swing(50) > swing(90) > swing(150)
