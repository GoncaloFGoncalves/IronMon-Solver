"""Upside: o valor do efeito secundario, que depende do mon e nao do move.

Nao ha formula por familia de efeito (GRUPOS.md C). O valor e o **swing na
troca**, e por isso o mesmo thunderbolt vale muito a um mon lento -- que a
paralisia converte em rapido -- e quase nada a um que ja era rapido.

Tres cenarios (CONTEXT.md 3.5b): o efeito nunca dispara, dispara sempre, e
dispara com a probabilidade real. O terceiro e o que conta; os outros dois
sao os limites e servem para ver quanto e que o efeito pode valer em teoria.

A probabilidade de ter disparado **ao menos uma vez** na troca e
`1 - (1-p)^turnos`, e nao `p`: um efeito de 10% com cinco turnos dispara em
41% das trocas.
"""

from dataclasses import dataclass, replace

from mon.battle import Combatant, win_probability
from mon.status import burned, confused, frozen, paralysed, poisoned

TURNS = 3   # duracao tipica de uma troca; parametro, nao constante do jogo


@dataclass(frozen=True)
class Upside:
    """O efeito secundario de um move, como o `move_meta` do veekun o da."""

    ailment: str = ""        # paralysis, burn, poison, freeze, confusion
    chance: float = 0.0      # probabilidade por golpe
    flinch: float = 0.0      # probabilidade de tirar o turno, por golpe


_AILMENTS = {
    "paralysis": lambda target, physical: paralysed(target),
    "poison": lambda target, physical: poisoned(target),
    "freeze": lambda target, physical: frozen(target),
    "confusion": lambda target, physical: confused(target),
    "burn": lambda target, physical: burned(target, physical),
}


def scenarios(me: Combatant, them: Combatant, upside: Upside,
              physical: bool = True, turns: int = TURNS):
    """(nunca dispara, dispara sempre, dispara com a probabilidade real)."""
    nunca = win_probability(me, them)
    alvo = them
    effect = _AILMENTS.get(upside.ailment)
    if effect is not None and upside.chance:
        alvo = effect(alvo, physical)
    # O flinch so tira turno a quem ataca em segundo: se eu sou mais lento,
    # ele ja agiu quando eu acerto. No cenario "dispara sempre" ele nunca age.
    if upside.flinch and me.speed > them.speed:
        alvo = replace(alvo, action_chance=0.0)
    sempre = win_probability(me, alvo)

    por_golpe = max(upside.chance, upside.flinch)
    ao_menos_uma = 1 - (1 - por_golpe) ** turns
    return nunca, sempre, nunca + ao_menos_uma * (sempre - nunca)


def value(me: Combatant, them: Combatant, upside: Upside,
          physical: bool = True, turns: int = TURNS) -> float:
    """O cenario real -- o que entra no score."""
    return scenarios(me, them, upside, physical, turns)[2]
