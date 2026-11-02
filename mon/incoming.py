"""O dano que levo: moves reais do adversario, nao um golpe neutro de 80.

O `pool.incoming_damage` tratava a ignorancia sobre os moves do adversario
como **ausencia de tipo**. Sao coisas diferentes: randomizado quer dizer com
uma distribuicao conhecida sobre os tipos. O resultado era que um Gyarados
(WATER/FLYING, x4 a ELECTRIC) e um Snorlax (NORMAL) com o mesmo BST e o mesmo
perfil levavam exactamente o mesmo dano (CONTEXT.md 4b).

O modelo, como o ruleset o define:

- o adversario tem **4 moves sorteados** do mesmo pool de 194;
- escolhe **a sorte entre os que matam de um**, e o que mais doi se nenhum
  mata;
- **o excesso e desperdicado** -- um move que faz 3x o meu HP nao vale mais
  do que um que faz exactamente o suficiente. Daqui sai o `lethal_cap`.
- itens nao contam, por decisao.

Do corte sai a forma do resultado. Depois de cortar, so ha duas situacoes
distinguiveis, e por isso a troca resolve-se **duas vezes** e nao uma:

  p       -- pelo menos um dos 4 mata de um: levo o `lethal_cap`
  1 - p   -- nenhum mata: levo o melhor de 4 tirados dos que sobram

Um escalar unico nao serve aqui. Com 13% de hipotese de morrer de um golpe e
87% de levar 40, a media da 56, que o motor leria como "tres golpes para me
matar" -- e nunca sao tres.
"""

from math import comb

import numpy as np

from mon.moves import PHYSICAL_TYPES
from mon.orderstat import subset_weights
from mon.typechart import GEN_2_TO_5

SLOTS = 4          # os 4 slots de um mon de treinador
MIN_ROLL = 85      # o roll minimo de Gen 3, em percentagem


def lethal_cap(hp: int) -> int:
    """O menor dano base que mata **em todos os 16 rolls**.

    Acima disto o dano extra nao pode mudar nada, e e onde o corte cai.
    """
    cap = -(-hp * 100 // MIN_ROLL)
    while cap * MIN_ROLL // 100 < hp:
        cap += 1
    return cap


def _damage_matrix(target, moves, pool) -> np.ndarray:
    """`(move, defensor)` -> o que cada move faz a `target` na mao de cada um.

    O STAB e a efectividade saem de matrizes que o `DefenderPool` precalcula
    por checkpoint; aqui so se indexa por tipo.
    """
    from mon.pool import _TYPE_INDEX
    level = pool.defenders[0].level
    factor = 2 * level // 5 + 2

    out = np.zeros((len(moves), len(pool.defenders)), dtype=np.int64)
    for index, move in enumerate(moves):
        physical = move.type in PHYSICAL_TYPES
        offence = pool.attack_both if physical else pool.special_attack
        defence = target.defense if physical else target.special_defense
        base = factor * move.power * offence // defence // 50 + 2
        row = _TYPE_INDEX[move.type]
        effectiveness = GEN_2_TO_5.effectiveness(move.type, target.types)
        out[index] = (base * pool.stab[row] * effectiveness).astype(np.int64)
    return out


def incoming_profile(target, moves, pool, slots: int = SLOTS, detail=False):
    """`(p_letal, dano_se_nao_letal)` por defensor.

    `p_letal` e hipergeometrico: tirados `slots` de `len(moves)`, a hipotese
    de pelo menos um estar entre os `k` que matam de um e
    `1 - C(M-k, slots) / C(M, slots)`.
    """
    raw = _damage_matrix(target, moves, pool)
    total = len(moves)
    cap = lethal_cap(target.hp)
    lethal = raw >= cap
    counts = lethal.sum(axis=0)
    left = total - counts

    # `share` e `safe` dependem do defensor so atraves de `left`, e `left` tem
    # no maximo 195 valores. Agrupa-se por valor em vez de chamar `comb` e
    # `subset_weights` 10 422 vezes: era 2.4x o custo da celula, agora e 1.4x.
    whole = comb(total, slots)
    ratio = np.array([comb(k, slots) / whole if k >= slots else 0.0
                      for k in range(total + 1)])
    share = 1.0 - ratio[left]

    # Os letais vao para o fundo como zeros para nao entrarem no melhor-de-N.
    survivors = np.sort(np.where(lethal, 0, raw), axis=0)
    safe = np.zeros(len(pool.defenders), dtype=np.int64)
    for value in np.unique(left):
        columns = np.flatnonzero(left == value)
        if value < slots:
            safe[columns] = cap
            continue
        weights = subset_weights(int(value), slots)[:, None]
        safe[columns] = (survivors[total - value:, columns]
                         * weights).sum(axis=0).astype(np.int64)

    if detail:
        return share, safe, raw
    return share, safe
