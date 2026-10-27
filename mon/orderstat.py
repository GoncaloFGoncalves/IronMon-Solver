"""Melhor de N moves aleatorios, sem simular sorteios.

No Kaizo os moves sao aleatorios: nao se escolhe de 194, calha-nos N. A
pergunta certa nao e "qual o melhor moveset possivel" mas "o que esperar do
que calhar" (CONTEXT.md 3.5b).

Se os N moves sao um subconjunto uniforme dos M do pool, a probabilidade de
o k-esimo pior ser o melhor dos N e `C(k, N-1) / C(M, N)` -- tem de ser
escolhido ele e os outros N-1 de entre os k que estao abaixo. Logo o valor
esperado do melhor e uma **soma pesada dos scores ordenados**, com pesos que
so dependem de (M, N). Nao ha amostragem e nao ha ruido.

Que o subconjunto seja o mesmo para todos os defensores nao altera o valor
esperado do agregado -- a media sobre defensores e linear, e por isso
trocar a ordem das duas e exato. Muda a variancia, nao a media.
"""

from functools import lru_cache
from math import comb

import numpy as np


@lru_cache(maxsize=None)
def subset_weights(pool_size: int, known: int) -> np.ndarray:
    """Peso de cada posicao do pool ordenado, do pior para o melhor."""
    known = max(1, min(known, pool_size))
    total = comb(pool_size, known)
    return np.array([comb(rank, known - 1) / total
                     for rank in range(pool_size)], dtype=np.float64)


def expected_best(scores: np.ndarray, known: int, companion: np.ndarray = None):
    """E[melhor de `known`] por coluna, com `scores` em (move, defensor).

    `companion` e um segundo valor que viaja com o move escolhido -- o HP
    restante. Reordena-se pela **mesma** permutacao do score, porque o move
    escolhe-se pelo score e nao pelo companion.
    """
    order = np.argsort(scores, axis=0, kind="stable")
    ranked = np.take_along_axis(scores, order, axis=0)
    weights = subset_weights(scores.shape[0], known)[:, None]
    best = (ranked * weights).sum(axis=0)
    if companion is None:
        return best
    together = np.take_along_axis(companion, order, axis=0)
    return best, (together * weights).sum(axis=0)
