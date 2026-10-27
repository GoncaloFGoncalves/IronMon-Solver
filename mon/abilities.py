"""Aproveitamento das habilidades: swing na batalha, nao valor de familia.

A habilidade entra depois do moveset (CONTEXT.md 3.5b): o mesmo Guts e
decisivo num mon fisico e nulo num special. Logo o valor nao e uma constante
por habilidade -- e o swing que provoca nesta troca, com este moveset.

Opcao (c): so as habilidades com mecanica modelada produzem swing; as
restantes valem zero em vez de valerem um palpite.

As regras de dungeon do IronMon entram como fator de aproveitamento. Nao ha
cura, nem PP, nem apanhar status a um mon selvagem, e por isso uma habilidade
que precisa de uma condicao que o jogador nao controla vale menos que o seu
swing bruto.
"""

from dataclasses import dataclass, replace

from mon.battle import Combatant, win_probability
from mon.status import BURN_RESIDUAL

GUTS_ATTACK_FACTOR = 1.5
RECOIL_FRACTION = 1 / 3        # double-edge e companhia, em Gen 3

# Burn e poison tiram 1/8 do HP por turno em Gen 3: ao oitavo turno o mon
# morre. Dentro de uma dungeon nao ha cura, logo e esta a janela toda.
GUTS_WINDOW_TURNS = int(1 / BURN_RESIDUAL)

# O status que o Guts precisa tem de ser oferecido pelo adversario: auto-
# inflingir obrigaria a itens ou a um mon selvagem, os dois fora das regras
# dentro de uma dungeon. Valor a calibrar em jogo (CONTEXT.md 6).
DUNGEON_SELF_STATUS = 0.25


@dataclass(frozen=True)
class MonContext:
    """O que a habilidade precisa de saber sobre o mon e a troca."""

    me: Combatant
    them: Combatant
    physical: bool = True            # o meu moveset bate por Atk
    recoil: bool = False             # tenho move de recuo
    incoming_physical: bool = True   # ele bate-me por Atk


def _guts(ctx):
    """1.5x de Atk, mas o status que o liga tira 1/8 do HP por turno."""
    if not ctx.physical:
        return None
    return (replace(ctx.me,
                    damage=ctx.me.damage * GUTS_ATTACK_FACTOR,
                    residual=ctx.me.residual + ctx.me.hp * BURN_RESIDUAL),
            ctx.them)


def _truant(ctx):
    return replace(ctx.me, action_chance=ctx.me.action_chance * 0.5), ctx.them


def _intimidate(ctx):
    if not ctx.incoming_physical:
        return None
    return ctx.me, replace(ctx.them, damage=ctx.them.damage * 0.5)


def _rock_head(ctx):
    """Sem move de recuo nao ha recuo para cortar."""
    if not ctx.recoil:
        return None
    recuo = ctx.me.damage * RECOIL_FRACTION
    return (replace(ctx.me, residual=ctx.me.residual + recuo),
            ctx.them), (ctx.me, ctx.them)


_EFFECTS = {
    "guts": _guts,
    "truant": _truant,
    "intimidate": _intimidate,
    "rock-head": _rock_head,
}

_FEASIBILITY = {"guts": DUNGEON_SELF_STATUS}


def swing(ability: str, ctx: MonContext) -> float:
    """score(efeito sempre) - score(efeito nunca), ignorando as dungeons.

    Zero quando a habilidade nao tem mecanica modelada ou quando a mecanica
    nao se aplica a este mon.
    """
    effect = _EFFECTS.get(ability)
    if effect is None:
        return 0.0
    altered = effect(ctx)
    if altered is None:
        return 0.0
    if isinstance(altered[0], tuple):   # a habilidade remove um custo
        pior, melhor = altered
        return win_probability(*melhor) - win_probability(*pior)
    return win_probability(*altered) - win_probability(ctx.me, ctx.them)


def utilization(ability: str, ctx: MonContext) -> float:
    """O swing descontado da acessibilidade da condicao dentro da dungeon."""
    return swing(ability, ctx) * _FEASIBILITY.get(ability, 1.0)
