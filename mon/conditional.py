"""Moves com condicao: a condicao e turnos, nao BP.

O BP e o parametro (CONTEXT.md 3.5b), e a condicao **nao se desconta do BP**.
Um brick-break de 75 nao vale o mesmo que um hyper-beam de 150 a cada dois
turnos: no turno morto o adversario ataca de graca, e as vezes o dobro do BP
corta um golpe ao numero de golpes necessarios e o turno morto sai gratis.
Qual dos dois acontece depende do HP do alvo, logo um "BP por turno" apagava
exatamente a informacao que decide.

Por isso o que esta aqui sao os **dados da condicao**; quem a resolve e o
`sequence.py`, turno a turno, com o estado do mon a atravessar os embates."""

from dataclasses import replace

from mon.battle import Combatant

# Dois turnos por golpe: carregam antes (solar-beam e companhia) ou recarregam
# depois (hyper-beam e companhia). Em Gen 3 nao ha excecoes de tempo.
TURNS_PER_HIT = {
    "hyper-beam": 2, "blast-burn": 2, "frenzy-plant": 2, "hydro-cannon": 2,
    "solar-beam": 2, "razor-wind": 2, "skull-bash": 2, "sky-attack": 2,
    "fly": 2, "dig": 2, "dive": 2, "bounce": 2,
}

# Prioridade -3 e quebra com qualquer dano recebido no turno.
ALWAYS_LAST = frozenset({"focus-punch"})


def turns_per_hit(move: str) -> int:
    """Turnos que o move consome por golpe. O `sequence.py` perde os restantes."""
    return TURNS_PER_HIT.get(move, 1)


def focus_punch(me: Combatant, them: Combatant) -> Combatant:
    """Ataca sempre depois dele e falha se ele me tocar.

    Logo so sai nos turnos em que ele nao age -- e por isso o seu valor e o
    do adversario estar paralisado, congelado ou confuso, nunca o dos 150 BP.
    """
    return replace(me,
                   speed=min(me.speed, them.speed) - 1,
                   action_chance=me.action_chance * (1 - them.action_chance))
