"""Efeitos de status de Gen 3, como transformacoes de um Combatant.

O upside de um move e o swing que provoca na troca (CONTEXT.md 3.5b), e o
swing so e calculavel se o status alterar o combate. Cada funcao aqui devolve
um Combatant novo com o efeito aplicado -- e dai o motor do battle.py faz o
resto sozinho.

Valores de Gen 3. A paralisia corta a Speed a 1/4 (so passou a 1/2 na Gen 7)
e o burn tira 1/8 do HP (passou a 1/16 na Gen 7).
"""

from dataclasses import replace

from mon.battle import Combatant

PARALYSIS_SPEED_FACTOR = 0.25
PARALYSIS_SKIP_CHANCE = 0.25
BURN_PHYSICAL_FACTOR = 0.5
BURN_RESIDUAL = 1 / 8
POISON_RESIDUAL = 1 / 8
FREEZE_THAW_CHANCE = 0.20
CONFUSION_SELF_HIT_CHANCE = 0.50


def paralysed(target: Combatant) -> Combatant:
    return replace(
        target,
        speed=target.speed * PARALYSIS_SPEED_FACTOR,
        action_chance=target.action_chance * (1 - PARALYSIS_SKIP_CHANCE),
    )


def burned(target: Combatant, physical: bool) -> Combatant:
    """O corte de Atk so vale para moves fisicos; o dano por turno e sempre."""
    damage = target.damage * BURN_PHYSICAL_FACTOR if physical else target.damage
    return replace(target, damage=damage,
                   residual=target.residual + target.hp * BURN_RESIDUAL)


def poisoned(target: Combatant) -> Combatant:
    return replace(target, residual=target.residual + target.hp * POISON_RESIDUAL)


def frozen(target: Combatant) -> Combatant:
    """So age quando descongela -- 20% por turno em Gen 3."""
    return replace(target, action_chance=target.action_chance * FREEZE_THAW_CHANCE)


def confused(target: Combatant) -> Combatant:
    """Metade dos turnos acerta em si proprio em vez de atacar (Gen 3)."""
    return replace(target,
                   action_chance=target.action_chance * (1 - CONFUSION_SELF_HIT_CHANCE))
