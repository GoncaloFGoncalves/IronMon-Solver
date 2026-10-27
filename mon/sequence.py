"""Batalhas em sequencia: o estado do mon atravessa os embates.

O `battle.py` fecha a conta de uma troca e devolve um numero. Isso nao chega
para uma dungeon: para encadear o mon seguinte e preciso saber *em que estado*
o mon ficou (CONTEXT.md 3.6b). Um snorlax que mata com double-edge ao primeiro
turno entra no mon seguinte com menos HP; um que mate com hyper-beam entra a
dever um turno. Sao estes estados que fazem a dungeon, nao a vitoria isolada.

O modelo e uma distribuicao de estados, nao um valor esperado. O valor esperado
dilui exatamente a informacao que interessa: 50% de probabilidade de chegar
inteiro e 50% de chegar morto nao e "metade do HP".

O que mantem o numero de entradas baixo e o **agrupamento**: o HP e arredondado
a uma grelha (`BUCKETS` niveis), e por isso dois caminhos que acabam quase no
mesmo HP colapsam num estado so. Sem isso, 16 rolls por golpe multiplicavam-se
turno a turno.
"""

from dataclasses import dataclass, replace
from functools import lru_cache

BUCKETS = 20          # grelha de HP: 5% do maximo
ROLLS = range(85, 101)
MAX_TURNS = 50        # uma troca que nao resolve ate aqui esta perdida


@dataclass(frozen=True)
class Fighter:
    """O que nao muda durante a secao: o perfil do mon e do seu move."""

    damage: float              # dano antes do roll
    hp: float
    speed: float
    pp: int = 99
    turns_per_hit: int = 1     # 2 nos moves que carregam ou recarregam
    recoil: float = 0.0        # fracao do dano causado que me volta
    drain: float = 0.0         # fracao do dano causado que me cura


@dataclass(frozen=True)
class State:
    """O que atravessa os embates."""

    hp: float
    pp: int
    owed: int = 0              # turnos que devo antes de voltar a atacar


@dataclass(frozen=True)
class Outcome:
    survival: float                  # probabilidade de chegar ao fim vivo
    states: dict                     # State -> probabilidade (soma = survival)

    def expected_hp(self) -> float:
        """HP medio de quem sobreviveu -- 0 se ninguem sobreviveu."""
        if not self.survival:
            return 0.0
        return sum(s.hp * p for s, p in self.states.items()) / self.survival


@lru_cache(maxsize=None)
def _rolls(base: float):
    """Os 16 danos possiveis, agrupados por valor igual.

    Em cache porque e chamado em cada ataque de cada estado de cada turno --
    medido, era a maior parte do tempo de uma secao de 6 mons.
    """
    out = {}
    for roll in ROLLS:
        value = int(base) * roll // 100
        out[value] = out.get(value, 0) + 1 / 16
    return tuple(out.items())


def _snap(hp: float, step: float) -> float:
    return round(hp / step) * step


def _act(fighter, state, hp_alvo, max_hp):
    """Um turno de um lado. Devolve (estado novo, hp do alvo, prob)."""
    if state.owed > 0:                       # turno morto: recarga ou truant
        return [(replace(state, owed=state.owed - 1), hp_alvo, 1.0)]
    if state.pp <= 0:                        # sem PP nao ha ataque possivel
        return [(state, hp_alvo, 1.0)]
    seguinte = replace(state, pp=state.pp - 1,
                       owed=fighter.turns_per_hit - 1)
    saidas = []
    for dano, prob in _rolls(fighter.damage):
        feito = min(dano, hp_alvo)           # recuo e dreno contam o dano real
        hp = seguinte.hp - feito * fighter.recoil + feito * fighter.drain
        hp = min(max_hp, hp)
        saidas.append((replace(seguinte, hp=hp), hp_alvo - dano, prob))
    return saidas


@lru_cache(maxsize=None)
def resolve(me: Fighter, them: Fighter, state: State = None,
            max_turns: int = MAX_TURNS) -> Outcome:
    """Uma troca, a partir de um estado e para uma distribuicao de estados.

    O recuo pode matar-me no mesmo turno em que mato: a ordem e a do jogo --
    o dano sai, depois o recuo. Quem ataca primeiro decide-se pela Speed, com
    o empate a sorte, e os dois ramos seguem em paralelo.
    """
    if state is None:
        state = State(hp=me.hp, pp=me.pp)
    step = me.hp / BUCKETS
    dist = {(state, State(hp=them.hp, pp=them.pp)): 1.0}
    vivos = {}
    primeiro = 1.0 if me.speed > them.speed else 0.0 if me.speed < them.speed else 0.5

    for _ in range(max_turns):
        novo = {}
        for (meu, dele), prob in dist.items():
            for eu_primeiro, p_ordem in ((True, primeiro), (False, 1 - primeiro)):
                if p_ordem == 0:
                    continue
                for ramo, p_ramo in _turno(me, them, meu, dele, eu_primeiro):
                    if ramo is None:                      # morri
                        continue
                    meu2, dele2 = ramo
                    p = prob * p_ordem * p_ramo
                    if dele2.hp <= 0:                     # ganhei a troca
                        fim = replace(meu2, hp=_snap(meu2.hp, step))
                        vivos[fim] = vivos.get(fim, 0.0) + p
                    else:
                        novo[(meu2, dele2)] = novo.get((meu2, dele2), 0.0) + p
        dist = novo
        if not dist:
            break
    return Outcome(sum(vivos.values()), vivos)


def _turno(me, them, meu, dele, eu_primeiro):
    """Os dois ataques de um turno, na ordem dada. None = morri."""
    ramos = [((meu, dele), 1.0)]
    for atacante in (("eu", "ele") if eu_primeiro else ("ele", "eu")):
        saidas = []
        for ramo, p in ramos:
            if ramo is None:              # ja morri: o ramo fica fechado
                saidas.append((None, p))
                continue
            m, d = ramo
            if d.hp <= 0:                 # ele ja caiu: o turno acaba aqui
                saidas.append(((m, d), p))
                continue
            if atacante == "eu":
                for m2, hp_dele, pr in _act(me, m, d.hp, me.hp):
                    if m2.hp <= 0:        # o recuo matou-me
                        saidas.append((None, p * pr))
                    else:
                        saidas.append(((m2, replace(d, hp=hp_dele)), p * pr))
            else:
                for d2, hp_meu, pr in _act(them, d, m.hp, them.hp):
                    if hp_meu <= 0:
                        saidas.append((None, p * pr))
                    else:
                        saidas.append(((replace(m, hp=hp_meu), d2), p * pr))
        ramos = [(r, p) for r, p in saidas]
    return ramos


def run_section(me: Fighter, opponents, state: State = None) -> Outcome:
    """Uma secao de dungeon: os oponentes em fila, o estado a atravessa-los.

    Sem cura e sem recarga de PP entre embates -- e isso que faz a secao ser
    mais que a soma das trocas.
    """
    if state is None:
        state = State(hp=me.hp, pp=me.pp)
    dist = {state: 1.0}
    for them in opponents:
        seguinte = {}
        for estado, prob in dist.items():
            out = resolve(me, them, estado)
            for novo, p in out.states.items():
                seguinte[novo] = seguinte.get(novo, 0.0) + prob * p
        dist = seguinte
        if not dist:
            break
    return Outcome(sum(dist.values()), dist)
