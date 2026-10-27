"""Calendario de aprendizagem: a QUE NIVEIS uma especie aprende moves.

Em Kaizo os moves sao sorteados, mas o calendario segue o vanilla -- se o
Snorlax aprende um move ao nivel 17 no FRLG, aprende um move (outro) ao nivel
17 na run. Logo o *numero* de moves que uma especie ja aprendeu a um dado
nivel e invariante entre runs, e e um dos tres invariantes da especie
(CONTEXT.md 1.1).

Regra validada contra um log real do randomizer: bate em 386 de 386 especies.
"""

GUARANTEED_AT_LEVEL_ONE = 4


def learn_schedule(vanilla_levels) -> tuple[int, ...]:
    """Os niveis a que a especie aprende moves, do calendario vanilla."""
    ones = sum(1 for level in vanilla_levels if level <= 1)
    later = sorted(level for level in vanilla_levels if level > 1)
    return tuple([1] * max(ones, GUARANTEED_AT_LEVEL_ONE) + later)


def moves_known_at(schedule, level: int) -> int:
    """Quantos moves a especie ja aprendeu por level-up a este nivel."""
    return sum(1 for learned_at in schedule if learned_at <= level)
