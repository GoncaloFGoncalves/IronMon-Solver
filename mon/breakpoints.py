"""Onde cai a linha de morte, por tipo: a cadeia de breakpoint.

A celula da camada 0 diz "ganho 96% das vezes". Nao diz o que me mata. Esta
tabela responde a outra pergunta, que e a que se faz a olhar para um
adversario: *o thunderbolt mata, mas o spark tambem?*

Para cada tipo, ordenam-se os moves desse tipo por dano e desce-se a escada
ate ao degrau onde a morte deixa de ser certa. O que esta acima e proibido
levar; o primeiro que falha e a margem.

O dano depende de quem atira o move, e isso nao esta determinado -- os moves
e os stats dos treinadores sao randomizados. Em vez de escolher um atacante,
dao-se **dois**: o tipico e o pior caso. A distincao entre "o spark mata-te
sempre" e "o spark so te mata se vier de um glass cannon" e a informacao.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from mon.damage import probability_of_ko
from mon.moves import PHYSICAL_TYPES
from mon.typechart import GEN_2_TO_5


@dataclass(frozen=True)
class Threat:
    """O atacante hipotetico: so os stats com que bate.

    Nao e um mon -- e um nivel de ameaca. Os percentis saem do pool de
    defensores ao nivel do checkpoint (ver `threat_levels`).
    """
    attack: int
    special_attack: int
    stab: float = 1.0


TYPICAL_PERCENTILE = 50
WORST_PERCENTILE = 90


@dataclass(frozen=True)
class ThreatPair:
    """Os dois niveis de ameaca de um checkpoint."""
    typical: Threat
    worst: Threat
    level: int


@lru_cache(maxsize=None)
def threat_levels(checkpoint: str) -> ThreatPair:
    """Os dois atacantes de referencia ao nivel adversario do checkpoint.

    O **tipico** e o percentil 50 sem STAB: os moves sao sorteados do pool
    inteiro, logo um move ELECTRIC cai quase sempre num mon que nao e
    ELECTRIC. O **pior caso** e o percentil 90 com STAB.

    Levanta `KeyError` num checkpoint que nao exista -- um nome errado tem de
    rebentar, nao devolver silenciosamente o primeiro split.
    """
    from mon.levels import opponent_levels
    from mon.trainers import SPLITS
    from mon.variants import variants
    from mon.veekun import load_species

    if checkpoint not in SPLITS:
        raise KeyError("checkpoint desconhecido: %s" % checkpoint)
    level = opponent_levels()[SPLITS.index(checkpoint)]
    pool = [v for species in load_species() for v in variants(species, level, 31)]
    attack = np.array([v.attack for v in pool])
    special = np.array([v.special_attack for v in pool])

    def at(percentile: int, stab: float) -> Threat:
        return Threat(attack=int(np.percentile(attack, percentile)),
                      special_attack=int(np.percentile(special, percentile)),
                      stab=stab)

    return ThreatPair(typical=at(TYPICAL_PERCENTILE, 1.0),
                      worst=at(WORST_PERCENTILE, 1.5), level=level)


# As constantes sao as do Koga, o checkpoint de referencia dos testes.
THREAT_TYPICAL = Threat(attack=95, special_attack=95, stab=1.0)
THREAT_WORST = Threat(attack=155, special_attack=155, stab=1.5)


@dataclass(frozen=True)
class Rung:
    """Um degrau: um move, o dano que faz e se mata."""
    move: str
    power: int
    damage: int     # antes do roll, nos inteiros do jogo
    ohko: float     # P(matar de 1)
    two: float      # P(matar de 2)


def chain(target, moves, move_type: str, threat: Threat, level: int,
          hp: int = None) -> list[Rung]:
    """Os moves de um tipo contra `target`, do que mais doi para o que menos.

    `level` e o do atacante, nao o do alvo: quem bate e o adversario.

    `hp` substitui o maximo do alvo, para perguntar **ferido**. E a diferenca
    entre uma tabela verdadeira e uma tabela util: na Misty nada de ELECTRIC
    mata este Gyarados aos 88 de HP, e aos 12 que lhe sobram de um thunderbolt
    matam-no 24% dos moves do pool inteiro. O dano nao muda -- muda o
    denominador.
    """
    hp = target.hp if hp is None else hp
    if hp <= 0:
        raise ValueError("hp tem de ser positivo, veio %r" % hp)
    physical = move_type in PHYSICAL_TYPES
    attack = threat.attack if physical else threat.special_attack
    defense = target.defense if physical else target.special_defense
    factor = 2 * level // 5 + 2
    effectiveness = GEN_2_TO_5.effectiveness(move_type, target.types)

    rungs = []
    for move in moves:
        if move.type != move_type:
            continue
        if effectiveness == 0:
            damage = 0
        else:
            base = factor * move.power * attack // defense // 50 + 2
            damage = int(base * threat.stab * effectiveness)
        rungs.append(Rung(
            move=move.name, power=move.power, damage=damage,
            ohko=probability_of_ko(damage, hp, 1),
            two=probability_of_ko(damage, hp, 2)))
    # Desempate pelo nome para a ordem ser estavel entre corridas.
    rungs.sort(key=lambda r: (-r.damage, r.move))
    return rungs


def breakpoint_of(rungs: list[Rung]) -> tuple[Rung | None, Rung | None]:
    """`(ultimo que mata sempre, primeiro que falha)`.

    Qualquer um pode ser `None`: um tipo que o alvo resiste nao tem degrau
    que mate, e um tipo que o mata todo nao tem degrau que falhe.
    """
    last = None
    for rung in rungs:
        if rung.ohko < 1.0:
            return last, rung
        last = rung
    return last, None


def chains_by_type(target, moves, threat: Threat, level: int,
                   hp: int = None) -> dict[str, list[Rung]]:
    """A cadeia de cada tipo que tenha pelo menos um move de dano."""
    return {move_type: chain(target, moves, move_type, threat, level, hp)
            for move_type in sorted({move.type for move in moves})}
