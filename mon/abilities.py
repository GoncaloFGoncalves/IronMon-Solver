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
# dentro de uma dungeon.
#
# Por **mon adversario**, derivado do pool e nao estimado: dos 193 moves de
# dano aprendiveis, 27 dao um status que o Guts aproveita (burn, poison,
# paralysis).
#
#   P(ter >=1 nos 4 slots)  = 1 - C(166,4)/C(193,4) = 0.4555
#   P(acertar em 3 turnos)  = media de 1-(1-c)^3    = 0.5065
#
# Ha teste que re-deriva este numero dos dados. O 0.25 que aqui estava era um
# palpite e calhou perto -- mas era por **dungeon**, nao por mon, e e nisso
# que estava errado: numa fila de 20 mons o status e praticamente certo.
STATUS_PER_MON = 0.2307


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

def self_status(mons: int) -> float:
    """P(chegar a ter status) ao longo de uma dungeon de `mons` adversarios.

    Satura depressa: 7 mons (o ginasio do Brock) dao 0.84 e 20 dao 0.995. Um
    valor fixo por dungeon dava ao Guts o mesmo valor numa sala de 2 e numa
    de 30, e a diferenca e entre valer um quarto e valer tudo.
    """
    if mons < 1:
        raise ValueError("uma dungeon tem pelo menos 1 mon, veio %r" % mons)
    return 1 - (1 - STATUS_PER_MON) ** mons


def guts_feasibility(mons: int) -> float:
    """P(apanhar status **e** chegar vivo ao fim da seccao para o aproveitar).

    Nao e o mesmo que `self_status`, e a diferenca e o ponto todo. O burn e o
    poison tiram 1/8 do HP por turno e dentro de uma dungeon nao ha cura: se
    o status cai ao primeiro de seis mons, morre-se ao terceiro. A janela sao
    8 turnos, ou seja ~2.7 mons, logo o status tem de cair **no fim** da fila.

    Por isso isto **decresce** com o tamanho da seccao -- de 0.41 numa fila de
    2 para 0.0003 no ginasio do Viridian. O `self_status` cresce, e usa-lo
    como viabilidade dizia que o Guts era melhor na fila longa.

    O status e **exogeno**: acontece com Guts ou sem ele, logo a habilidade
    nunca e um passivo. O que ela nao faz e salvar quem ja morreu.
    """
    if mons < 1:
        raise ValueError("uma dungeon tem pelo menos 1 mon, veio %r" % mons)
    from mon.upside import TURNS
    total = 0.0
    for first in range(1, mons + 1):
        # Sobram estes mons para aguentar com o status em cima, o proprio
        # incluido; se a conta do residual passa de 1, nao se chega ao fim.
        remaining = (mons - first + 1) * TURNS
        if remaining * BURN_RESIDUAL < 1:
            total += (1 - STATUS_PER_MON) ** (first - 1) * STATUS_PER_MON
    return total


# Habilidades cuja viabilidade depende do tamanho da dungeon. As que nao
# estao aqui valem 1: a mecanica aplica-se ou nao, e nao espera por nada.
_FEASIBILITY = {"guts": guts_feasibility}


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


DEFAULT_MONS = 7   # a sala do Brock, a mais curta das doze


def utilization(ability: str, ctx: MonContext, mons: int = DEFAULT_MONS) -> float:
    """O swing descontado da acessibilidade da condicao dentro da dungeon.

    `mons` e o numero de adversarios seguidos da seccao -- de 7 (Pewter) a 30
    (Viridian), pelo `gauntlet.dungeon_mons`. O valor por omissao e o mais
    curto, que e o desconto maior: um mon que so se aproveita numa fila longa
    nao devia parecer bom por omissao.
    """
    feasibility = _FEASIBILITY.get(ability)
    if feasibility is None:
        return swing(ability, ctx)
    return swing(ability, ctx) * feasibility(mons)
