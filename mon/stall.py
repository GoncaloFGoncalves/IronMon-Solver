"""A parede: um adversario que eu nao consigo ferir, e que se resolve a PP.

E o unico caso em que o numero de turnos nao tem limite natural -- nenhum dos
dois derruba o outro -- e por isso nao cabe no `vector.py`, que corta aos 6.

O caso canonico e o Shedinja, e ele e **unico**: a Wonder Guard esta banida
em todos os mons menos nele, logo e o unico do jogo a quem so os
super-efetivos tocam. Contra BUG/GHOST isso deixa 5 tipos uteis -- FLYING,
ROCK, GHOST, FIRE, DARK -- e **156 dos 194 moves de dano nao servem**. Com 4
moves sorteados sao 41% de hipotese de nao ter resposta; com 10 conhecidos,
11%; com 19, 1.3%.

Sem a habilidade, so o tipo ja o torna imune a NORMAL e FIGHTING, 72 dos 194.
O modelo e o do caso geral -- qualquer adversario cujo dano recebido seja
zero -- mas na pratica o Shedinja e quem o ocupa.

**Como se resolve, e nao e como parece.** O Struggle em Gen 3 e *typeless*
desde Gen 2: nao e NORMAL, e neutro contra tudo, e a Wonder Guard nao o
bloqueia. Logo ficar sem PP **nao** e perder -- o meu Struggle acerta no
Shedinja e 1 de HP morre com qualquer coisa. O recuo e 1/4 do **dano
causado**, nao do HP maximo (isso e Gen 4 em diante).

Daqui sai a forma do problema: quem fica sem PP primeiro resolve o embate.

- o PP **dele** acaba primeiro -> ele da Struggle, leva 1/4 do dano que
  causou, e com 1 de HP morre. Eu nem preciso de o ferir.
- o PP **meu** acaba primeiro -> eu dou Struggle, que o atinge, e ele morre.

Em qualquer dos casos ganho o embate **se sobreviver aos turnos que isso
leva**. E e essa a conta: `min(meu PP, PP dele)` turnos a levar dano.

**O custo nao e a vitoria, e o PP.** Fora de uma dungeon cura-se e recarrega-
se, logo a parede e so "sobrevivo ou nao". Dentro de uma dungeon saio do
embate com **zero PP**, e o resto da seccao faz-se a Struggle -- 60 turnos de
stall gastam o orcamento todo. E ai que a run acaba, nao no embate.

Referencias: Struggle e Recoil na Bulbapedia (CONTEXT.md 6).
"""

from dataclasses import dataclass
from math import comb

from mon.damage import probability_of_ko

STRUGGLE_POWER = 50
STRUGGLE_RECOIL = 1 / 4   # do dano causado, nao do HP maximo


@dataclass(frozen=True)
class Wall:
    """Um adversario que eu nao consigo ferir, e o que cada lado tem."""

    my_hp: int
    my_pp: int          # PP somado dos meus moves
    their_hp: int
    their_damage: int   # dano base dele contra mim, por turno
    their_pp: int       # PP somado dos moves de dano dele
    struggle: int       # dano base do meu Struggle contra ele


@dataclass(frozen=True)
class Stall:
    survival: float     # P(chegar ao fim do embate vivo)
    hp_left: float      # E[HP restante | sobrevivo]
    pp_left: int        # PP que sobra -- zero quando fui eu a dar Struggle
    turns: int          # turnos ate o embate resolver
    struggled: str      # "me" ou "them": quem ficou sem PP primeiro


def resolve(wall: Wall) -> Stall:
    """O desfecho de um embate contra uma parede.

    Levanta `ValueError` se o meu Struggle nao a mata: nesse caso nao e uma
    parede, e um empate verdadeiro, e o modelo nao tem resposta para isso --
    melhor rebentar do que devolver um numero inventado.
    """
    if wall.struggle <= 0:
        raise ValueError("sem Struggle que a fira nao ha desfecho")

    # Empate no PP resolve-se a meu favor: ataco no mesmo turno e o meu
    # Struggle mata-o antes de o dele importar.
    mine_first = wall.my_pp <= wall.their_pp
    struggled = "me" if mine_first else "them"
    # Os turnos em que levo dano: o PP que se esgota, mais o turno do Struggle.
    turns = min(wall.my_pp, wall.their_pp) + 1

    died = probability_of_ko(wall.their_damage, wall.my_hp, turns)
    survival = 1.0 - died
    if survival <= 0.0:
        return Stall(0.0, 0.0, 0, turns, struggled)

    # O HP restante e aproximado pelo dano medio por golpe, como no
    # `vector.trade`: a distribuicao exacta sobre 60 turnos nao acrescenta
    # nada a uma consulta e custa a convolucao toda.
    from mon.damage import _hit_damages
    mean_hit = sum(_hit_damages(wall.their_damage)) / 16
    spent = turns * mean_hit
    if mine_first:
        # O meu Struggle tambem me cobra: 1/4 do dano que causei.
        spent += wall.struggle * STRUGGLE_RECOIL
    hp_left = max(0.0, wall.my_hp - spent)
    pp_left = 0 if mine_first else wall.their_pp - wall.my_pp
    return Stall(survival, hp_left, max(0, pp_left), turns, struggled)


def no_coverage_chance(useless: int, pool: int, known: int) -> float:
    """P(nenhum dos `known` moves sorteados ferir esta parede).

    Hipergeometrico: tirados `known` de `pool`, a hipotese de **todos** virem
    dos `useless` que nao a afectam. Contra BUG/GHOST sao 72 de 194 pelo
    tipo (1.8% com 4 moves) ou 156 de 194 com Wonder Guard (41%).
    """
    if known > useless:
        return 0.0
    return comb(useless, known) / comb(pool, known)
