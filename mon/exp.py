"""EXP e curvas de crescimento: o nivel esperado em cada split.

O nivel nao depende da especie, depende da **curva** (CONTEXT.md 3.3). Sao 6
curvas para 386 especies, e por isso simula-se 6 vezes e nao 386.

A formula de Gen 3 nao escala com a diferenca de niveis: `exp = base x L / 7`,
e os treinadores dao 1.5x. Sem escala por diferenca, um mon sobrenivelado nao
e penalizado -- o que importa e o nivel de **quem cai**.
"""

from functools import lru_cache

from mon.veekun import load_table

# A disassembly e o veekun nao usam os mesmos nomes para as curvas.
CURVES = {
    "MEDIUM_FAST": "medium",
    "MEDIUM_SLOW": "medium-slow",
    "SLOW": "slow",
    "FAST": "fast",
    "ERRATIC": "slow-then-very-fast",
    "FLUCTUATING": "fast-then-very-slow",
}

TRAINER_BONUS = (3, 2)   # 1.5x, em inteiros

# O randomizer do Kaizo padroniza a curva de **todos** os mons. Nao ha 6
# curvas para simular -- ha uma. As outras ficam no `CURVES` porque o jogo
# base as tem e o `thresholds` serve para qualquer uma.
STANDARD_CURVE = "FLUCTUATING"


@lru_cache(maxsize=None)
def thresholds(curve: str) -> tuple[int, ...]:
    """EXP acumulado necessario para cada nivel, indexado pelo nivel."""
    identifier = CURVES[curve]
    rate_id = next(row["id"] for row in load_table("growth_rates")
                   if row["identifier"] == identifier)
    by_level = {int(row["level"]): int(row["experience"])
                for row in load_table("experience")
                if row["growth_rate_id"] == rate_id}
    return tuple([0] + [by_level[level] for level in sorted(by_level)])


def level_at(curve: str, experience: int) -> int:
    """O nivel que esse EXP acumulado da. Nunca passa dos 100."""
    table = thresholds(curve)
    for level in range(len(table) - 1, 0, -1):
        if experience >= table[level]:
            return level
    return 1


def exp_from_defeating(base_exp: int, level: int, trainer: bool = True) -> int:
    """EXP de derrubar um mon de `level`, com um so participante."""
    gained = base_exp * level // 7
    if trainer:
        gained = gained * TRAINER_BONUS[0] // TRAINER_BONUS[1]
    return gained
