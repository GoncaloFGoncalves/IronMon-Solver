"""A parede: um adversario que eu nao consigo ferir, e que se resolve a PP.

E o unico caso em que o numero de turnos nao tem limite natural -- nenhum dos
dois derruba o outro -- e por isso nao cabe no `vector.py`, que corta aos 6.

O caso canonico e o Shedinja, e ele e **unico**: a Wonder Guard esta banida
em todos os mons menos nele, logo e o unico do jogo a quem so os
super-efetivos tocam. Contra BUG/GHOST isso deixa 5 tipos uteis -- FLYING,
ROCK, GHOST, FIRE, DARK -- e **155 dos 193 moves de dano nao servem**. Com 4
moves sorteados sao 41% de hipotese de nao ter resposta; com 10 conhecidos,
10.5%; com 19, 1.2%.

Sem a habilidade, so o tipo ja o torna imune a NORMAL e FIGHTING, 71 dos 193.
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
    their_struggle: int = 0   # o Struggle dele contra mim; 0 = igual ao dano

    @property
    def struggle_back(self) -> int:
        return self.their_struggle or self.their_damage


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

    if mine_first:
        # Ele tem PP para todos os turnos: sao `turns` golpes normais dele.
        died = probability_of_ko(wall.their_damage, wall.my_hp, turns)
    else:
        # O PP dele acaba antes: `their_pp` golpes normais, e depois um
        # Struggle, que e um dano diferente. Convolui-se exacto em vez de
        # fingir que o ultimo golpe e igual aos outros -- com `their_pp = 0`
        # (sem moves de dano) e literalmente o unico golpe que levo.
        died = _mixed_ko(wall.their_damage, wall.their_pp,
                         wall.struggle_back, wall.my_hp)
    survival = 1.0 - died
    if survival <= 0.0:
        return Stall(0.0, 0.0, 0, turns, struggled)

    # O HP restante e aproximado pelo dano medio por golpe, como no
    # `vector.trade`: a distribuicao exacta sobre 60 turnos nao acrescenta
    # nada a uma consulta e custa a convolucao toda.
    from mon.damage import _hit_damages
    if mine_first:
        spent = turns * sum(_hit_damages(wall.their_damage)) / 16
        # O meu Struggle tambem me cobra: 1/4 do dano que causei.
        spent += wall.struggle * STRUGGLE_RECOIL
    else:
        spent = (wall.their_pp * sum(_hit_damages(wall.their_damage)) / 16
                 + sum(_hit_damages(wall.struggle_back)) / 16)
    hp_left = max(0.0, wall.my_hp - spent)
    pp_left = 0 if mine_first else wall.their_pp - wall.my_pp
    return Stall(survival, hp_left, max(0, pp_left), turns, struggled)


def _mixed_ko(damage: int, hits: int, last: int, hp: float) -> float:
    """P(`hits` golpes de `damage` mais um de `last` somarem `hp` ou mais).

    Exacto: convolui-se a distribuicao dos `hits` golpes com os 16 rolls do
    ultimo. Com `hits = 0` reduz-se a um golpe so, que e o caso de um
    adversario sem moves de dano.
    """
    from mon.damage import ROLLS, _hit_damages, _totals

    tail = _hit_damages(last) if last > 0 else (0,)
    if hits <= 0:
        return sum(1 for value in tail if value >= hp) / len(tail)
    totals = _totals(int(damage), hits)
    span = len(ROLLS) ** hits * len(tail)
    favourable = sum(count for total, count in totals
                     for value in tail if total + value >= hp)
    return favourable / span


def no_coverage_chance(useless: int, pool: int, known: int) -> float:
    """P(nenhum dos `known` moves sorteados ferir esta parede).

    Hipergeometrico: tirados `known` de `pool`, a hipotese de **todos** virem
    dos `useless` que nao a afectam. Contra BUG/GHOST sao 71 de 193 pelo
    tipo (1.7% com 4 moves) ou 155 de 193 com Wonder Guard (41%).
    """
    if known > useless:
        return 0.0
    return comb(useless, known) / comb(pool, known)


@dataclass(frozen=True)
class PartyOutcome:
    """O embate inteiro, com a parede num slot."""

    survival: float          # P(chegar ao fim do treinador vivo)
    struggling_after: int    # mons que enfrento depois, ja sem PP
    hp_entering: float       # HP com que chego a parede
    hp_left: float           # HP com que saio do treinador, se sair


def party_outcome(wall_at: int, size: int, *, my_hp: int, my_pp: int,
                  my_damage: int, my_speed: int, my_struggle: int,
                  their_hp: int, their_damage: int, their_pp: int,
                  their_struggle: int, other_hp: int, other_damage: int,
                  other_speed: int) -> PartyOutcome:
    """O desfecho de um treinador que tem a parede no slot `wall_at`.

    A posicao muda tudo, e nos dois sentidos. Ao **slot 1** chego inteiro,
    gasto o PP todo a resolver a parede, e faco os outros cinco a Struggle --
    50 de power e 1/4 de recuo por golpe. Ao **slot 6** chego gasto, com
    menos HP para aguentar os turnos do stall, mas nao sobra nada para lutar
    depois.

    Os mons que nao sao a parede sao todos iguais ao mediano: e a estrutura
    que se quer ver, nao o numero exacto.
    """
    from mon.sequence import Fighter, State, run_section

    if not 1 <= wall_at <= size:
        raise ValueError("slot %r fora de uma equipa de %d" % (wall_at, size))

    other = Fighter(damage=float(other_damage), hp=float(other_hp),
                    speed=float(other_speed))
    armed = Fighter(damage=float(my_damage), hp=float(my_hp),
                    speed=float(my_speed), pp=my_pp)

    before = run_section(armed, [other] * (wall_at - 1))
    if not before.survival:
        return PartyOutcome(0.0, size - wall_at, 0.0, 0.0)
    hp_entering = before.expected_hp()
    pp_entering = (min(s.pp for s in before.states) if before.states
                   else my_pp)

    wall = Wall(my_hp=int(hp_entering), my_pp=int(pp_entering),
                their_hp=their_hp, their_damage=their_damage,
                their_pp=their_pp, struggle=my_struggle,
                their_struggle=their_struggle)
    stalled = resolve(wall)
    survival = before.survival * stalled.survival
    if not survival:
        return PartyOutcome(0.0, size - wall_at, hp_entering, 0.0)

    rest = size - wall_at
    if not rest:
        return PartyOutcome(survival, 0, hp_entering, stalled.hp_left)

    # Depois da parede o PP esta a zero: os que faltam fazem-se a Struggle,
    # que custa 1/4 do dano causado a cada golpe.
    struggling = Fighter(damage=float(my_struggle), hp=float(my_hp),
                         speed=float(my_speed), recoil=STRUGGLE_RECOIL)
    after = run_section(struggling, [other] * rest,
                        State(hp=max(1.0, stalled.hp_left),
                              pp=max(1, stalled.pp_left) if stalled.pp_left
                              else 99))
    return PartyOutcome(survival * after.survival, rest, hp_entering,
                        after.expected_hp())
