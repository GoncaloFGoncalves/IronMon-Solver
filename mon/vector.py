"""O caminho de score vectorizado. Sem isto a camada 0 nao corre.

Medido: 1.0x10^7 avaliacoes/s aqui contra 33 mil/s no `battle.py`. A camada 0
sao 1.3x10^12 avaliacoes (CONTEXT.md 3.7) -- 37 h assim, 450 dias em Python.
A vectorizacao nao e otimizacao, e a condicao de isto correr.

A tabela indexa `(dano antes do roll, turnos, hp)` e devolve a probabilidade
de KO. E construida por convolucao dos danos **truncados golpe a golpe**, a
mesma aritmetica do `damage.py` -- ha teste de concordancia, porque foi
precisamente uma divergencia entre dois caminhos que apanhou o bug do secao 5.
"""

from functools import lru_cache

import numpy as np

ROLLS = np.arange(85, 101)
MAX_DAMAGE = 900      # acima disto o roll minimo ja passa o HP maximo
MAX_HP = 700          # HP maximo possivel: BST 550 todo em HP, nivel 94
MAX_TURNS = 6


def ko_table(hit_chances=((1, 1.0),), max_turns: int = MAX_TURNS):
    """`tabela[dano, turnos, hp]` = P(KO), para uma distribuicao de golpes.

    `hit_chances` sao os golpes por turno: um move de 2-5 golpes sorteia a
    contagem em cada turno, logo entra aqui e nao no numero de turnos. So ha
    quatro distribuicoes em todo o pool, por isso quatro tabelas bastam.
    """
    if isinstance(hit_chances, dict):
        hit_chances = tuple(sorted(hit_chances.items()))
    return _ko_table(hit_chances, max_turns)


@lru_cache(maxsize=None)
def _ko_table(hit_chances: tuple, max_turns: int):
    table = np.zeros((MAX_DAMAGE + 1, max_turns + 1, MAX_HP + 1), dtype=np.float32)
    for damage in range(1, MAX_DAMAGE + 1):
        hits = (damage * ROLLS) // 100
        per_turn = _per_turn(hits, hit_chances)
        accumulated = np.array([1.0])
        for turn in range(1, max_turns + 1):
            accumulated = np.convolve(accumulated, per_turn)
            # P(total >= hp), para cada hp de uma vez
            survives = np.cumsum(accumulated[::-1])[::-1]
            width = min(len(survives), MAX_HP + 1)
            table[damage, turn, :width] = survives[:width]
    return table


def _per_turn(hits, hit_chances):
    """Distribuicao do dano de **um** turno, somando os golpes desse turno."""
    spread = np.zeros(hits.max() * max(h for h, _ in hit_chances) + 1)
    single = np.zeros(hits.max() + 1)
    np.add.at(single, hits, 1 / len(ROLLS))
    for count, chance in hit_chances:
        turn = np.array([1.0])
        for _ in range(count):
            turn = np.convolve(turn, single)
        spread[:len(turn)] += chance * turn
    return spread


def win_probabilities(damage, hp, odamage, ohp, speed, ospeed,
                      table=None, otable=None):
    """P(eu derrubar primeiro), para arrays inteiros e sem loops em Python.

    Quem ataca primeiro sai da Speed, com o empate a meias -- os dois ramos
    somam-se ponderados, igual ao `battle.py`.

    Tres detalhes que valem 3x no debito, medidos: indexar uma vista plana com
    um `take` de um eixo em vez de tres arrays de indices; reaproveitar o
    acumulado do turno anterior em vez de o reler; e acumular em float32.
    """
    table = ko_table() if table is None else table
    otable = table if otable is None else otable
    damage, odamage = _clip(damage), _clip(odamage)
    hp = np.minimum(hp, MAX_HP).astype(np.intp)
    ohp = np.minimum(ohp, MAX_HP).astype(np.intp)
    first = np.where(speed > ospeed, 1.0, np.where(speed < ospeed, 0.0, 0.5))
    first = first.astype(np.float32)

    turns = table.shape[1]
    per_damage = turns * (MAX_HP + 1)
    mine = table.reshape(-1)
    theirs = otable.reshape(-1)
    at_me = damage.astype(np.intp) * per_damage + ohp        # eu contra ele
    at_them = odamage.astype(np.intp) * per_damage + hp      # ele contra mim

    total = np.zeros(len(damage), dtype=np.float32)
    before = mine.take(at_me)                      # turno 0: ninguem caiu
    survives_first = 1 - theirs.take(at_them)
    for turn in range(1, turns):
        now = mine.take(at_me + turn * (MAX_HP + 1))
        survives_second = 1 - theirs.take(at_them + turn * (MAX_HP + 1))
        total += (now - before) * (first * survives_first
                                   + (1 - first) * survives_second)
        before = now
        survives_first = survives_second           # o de agora serve o proximo
    return total


@lru_cache(maxsize=None)
def _mean_hit() -> "np.ndarray":
    """Dano medio de um golpe, por dano antes do roll. Lookup, nao aritmetica."""
    return np.array([((damage * ROLLS) // 100).mean()
                     for damage in range(MAX_DAMAGE + 1)], dtype=np.float32)


def defender_curves(hp, odamage, table=None):
    """O lado do defensor, que nao depende do meu move.

    Devolve (P(ele me derrubar ate ao turno n), dano medio do golpe dele).
    Calcula-se **uma vez por atacante** e reutiliza-se nos 194 moves: era
    metade do tempo quando era refeito por move.
    """
    table = ko_table() if table is None else table
    hp = min(int(hp), MAX_HP)
    odamage = np.minimum(odamage, MAX_DAMAGE).astype(np.intp)
    killed = np.stack([table[:, turn, hp].take(odamage)
                       for turn in range(table.shape[1])])
    return killed, _mean_hit().take(odamage)


def trade(damage, hp, odamage, ohp, first, table=None, otable=None,
          curves=None):
    """(P(ganhar), E[HP restante | ganhar]) -- o conteudo de uma celula.

    O HP restante e a moeda da sobrevivencia (CONTEXT.md 3.6b): se eu derrubo
    ao turno n, ele atacou n ou n-1 vezes, e o dano medio por golpe e um
    lookup. Erra menos de 1 HP contra o motor exacto -- ha teste.

    `first` e a probabilidade de eu atacar primeiro, escalar ou por defensor.
    `damage` tambem pode variar por defensor: o meu golpe nao faz o mesmo a
    todos. `curves` evita recalcular o lado do defensor por cada move.

    O que **nao** conta: PP a esgotar-se, cura de dreno, status a atravessar
    embates. Isso e o `sequence.py`, e fica para consulta.
    """
    table = ko_table() if table is None else table
    hp = min(int(hp), MAX_HP)
    ohp = np.minimum(ohp, MAX_HP).astype(np.intp)
    killed, mean_hit = (defender_curves(hp, odamage, otable or table)
                        if curves is None else curves)

    rows = _Rows(table, damage, ohp)
    won = np.zeros(len(ohp), dtype=np.float64)
    hp_left = np.zeros(len(ohp), dtype=np.float64)
    before = rows.at(0)
    for turn in range(1, table.shape[1]):
        now = rows.at(turn)
        landed = now - before
        # Se eu ataco primeiro ele deu turn-1 golpes quando cai; se ataco
        # depois, deu turn. Os dois ramos somam-se pesados pelo `first`.
        as_first = landed * (1 - killed[turn - 1]) * first
        as_second = landed * (1 - killed[turn]) * (1 - first)
        won += as_first + as_second
        hp_left += (as_first * np.maximum(hp - (turn - 1) * mean_hit, 0)
                    + as_second * np.maximum(hp - turn * mean_hit, 0))
        before = now
    return won, np.divide(hp_left, won, out=np.zeros_like(hp_left), where=won > 0)


class _Rows:
    """Le a tabela com o dano constante ou variavel, sem ramificar no ciclo.

    O dano do atacante **nao** e constante sobre o pool: muda com a defesa e
    com a efetividade de cada defensor. Com um escalar a tabela colapsa numa
    fatia que cabe em cache (1.5x10^7/s); com um array e um take plano sobre
    a vista inteira (7x10^6/s). Os dois dao o mesmo numero.
    """

    def __init__(self, table, damage, ohp):
        self.width = table.shape[2]
        if np.isscalar(damage) or np.ndim(damage) == 0:
            self.slice = table[min(int(damage), MAX_DAMAGE)]
            self.flat = None
            self.ohp = ohp
        else:
            self.flat = table.reshape(-1)
            per_damage = table.shape[1] * self.width
            damage = np.minimum(damage, MAX_DAMAGE).astype(np.intp)
            self.base = damage * per_damage + ohp

    def at(self, turn):
        if self.flat is None:
            return self.slice[turn].take(self.ohp)
        return self.flat.take(self.base + turn * self.width)


def win_block(damage, hp, odamage, ohp, first, table=None, otable=None):
    """So a probabilidade de ganhar. E o `trade` sem a moeda da sobrevivencia.

    Mantem-se porque e o que o `abilities.py` e as medicoes de swing querem,
    e porque dois caminhos a responder ao mesmo e como se apanhou o bug do
    secao 5 -- mas o calculo e um so.
    """
    return trade(damage, hp, odamage, ohp, first, table, otable)[0]


def _clip(damage):
    """Dano acima da tabela e OHKO garantido, logo cortar e exato."""
    return np.minimum(damage, MAX_DAMAGE)
