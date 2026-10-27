"""Probabilidade de KO, pela distribuicao exata dos rolls de dano.

Em Gen 3 o dano e multiplicado por um inteiro aleatorio de 85 a 100 (dividido
por 100), uniforme. O que interessa num combate nao e o dano medio mas um
limiar -- "mata em 2 golpes ou em 3" -- e a media erra grosseiramente nesse
limiar: com dano medio de 50% do HP, o valor esperado diz 2HKO e a
probabilidade real e 0.4%.

Ver CONTEXT.md 3.6.
"""

from functools import lru_cache

ROLLS = range(85, 101)


@lru_cache(maxsize=None)
def _hit_damages(base_damage: int) -> tuple[int, ...]:
    """Os 16 danos possiveis de um golpe, cada um truncado sozinho.

    **Truncar golpe a golpe nao e o mesmo que truncar a soma.** O jogo
    aplica o roll e trunca a cada golpe, e por isso a distribuicao do dano
    acumulado depende do `base_damage`, nao so de `hp / base_damage`. Era
    aqui que estava o bug: somar os rolls e aplicar o dano uma vez dava
    0.500 onde o valor real e 0.367 (3 golpes de base 36 contra 100 de HP),
    e os 13 pp propagavam-se ao `win_probability`.
    """
    return tuple(base_damage * roll // 100 for roll in ROLLS)


@lru_cache(maxsize=None)
def _totals(base_damage: int, hits: int) -> tuple[tuple[int, int], ...]:
    """Distribuicao exata do dano acumulado em `hits` golpes: (total, casos)."""
    dist = {0: 1}
    for _ in range(hits):
        grown = {}
        for total, count in dist.items():
            for damage in _hit_damages(base_damage):
                grown[total + damage] = grown.get(total + damage, 0) + count
        dist = grown
    return tuple(dist.items())


# Um move de 2-5 golpes sorteia a contagem em cada turno. Em Gen 3 a
# distribuicao e 3/8, 3/8, 1/8, 1/8 -- 2 e 3 golpes valem 75% das vezes.
HITS_TWO_TO_FIVE = {2: 0.375, 3: 0.375, 4: 0.125, 5: 0.125}


def probability_of_ko(base_damage: float, hp: float, hits: int) -> float:
    """Probabilidade de `hits` golpes derrubarem um defensor com `hp`.

    `base_damage` e o dano ANTES do roll aleatorio -- o valor maximo. Cada
    golpe causa `floor(base_damage * roll / 100)`, com o roll entre 85 e 100.
    """
    if hits <= 0 or base_damage <= 0:
        return 0.0
    totals = _totals(int(base_damage), hits)
    favourable = sum(count for total, count in totals if total >= hp)
    return favourable / len(ROLLS) ** hits


@lru_cache(maxsize=None)
def _strikes_in(turns: int, chances: tuple) -> tuple[tuple[int, float], ...]:
    """Distribuicao do numero total de golpes depois de `turns` turnos.

    A contagem sorteia-se **em cada turno**, logo o total e uma soma aleatoria
    e nao a media multiplicada pelos turnos.
    """
    dist = {0: 1.0}
    for _ in range(turns):
        grown = {}
        for total, p in dist.items():
            for hits, chance in chances:
                grown[total + hits] = grown.get(total + hits, 0.0) + p * chance
        dist = grown
    return tuple(dist.items())


def probability_of_ko_multi(base_damage: float, hp: float, turns: int,
                            hit_chances: dict) -> float:
    """Como o `probability_of_ko`, mas com varios golpes por turno.

    Cada golpe e truncado sozinho (ver `_hit_damages`), e por isso um turno de
    dois golpes de 30 **nao** e um golpe de 60: sao dois truncamentos. E a
    razao por que o BP nominal de um bullet-seed ou de um double-kick engana
    nos dois sentidos.
    """
    if turns <= 0 or base_damage <= 0:
        return 0.0
    chances = tuple(sorted(hit_chances.items()))
    return sum(p * probability_of_ko(base_damage, hp, strikes)
               for strikes, p in _strikes_in(turns, chances))
