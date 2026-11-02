"""Um ginasio e uma **fila** sem cura, nao uma batalha.

O `dungeons.py` conta batalhas obrigatorias. Isso subestima o ginasio por
duas vezes: o lider tem 5 ou 6 mons, e antes dele estao os treinadores da
sala. O Brock nao e "um embate" -- sao 7 mons seguidos, os 2 do Camper Liam
e os 5 dele, sem cura nem recarga de PP pelo meio.

Isto importa porque o mon que chega ao lider quase nunca chega a 100%: a
tabela de breakpoints (3.6d) muda toda quando o denominador e o HP que
sobra, e e o `sequence.py` que sabe propagar esse HP de embate em embate.

Conta-se **toda a sala, por regra do desafio**: dentro de um ginasio luta-se
com todos. Nao se infere do mapa, e isso importa -- o sinal que o mapa da e o
movimento, e em Kanto so um treinador de ginasio e spinner (o Juggler Kayden,
no Koga). Por esse criterio quase todos ficariam de fora.

O `leader_only` existe so para medir o que o modelo antigo perdia.
"""

from dataclasses import dataclass

from mon.trainers import LEADERS

# O Elite 4 nao e um ginasio e nao entra: nao tem sala com treinadores.
GYM_AREAS = {
    "brock": "Pewter Gym",
    "misty": "Cerulean Gym",
    "surge": "Vermillion Gym",
    "erika": "Celadon Gym",
    "koga": "Fuschia Gym",
    "sabrina": "Saffron Gym",
    "blaine": "Cinnabar Gym",
    "giovanni": "Viridian Gym",
}


@dataclass(frozen=True)
class Stage:
    """Um treinador da fila, com a equipa que poe."""
    trainer: str
    levels: tuple[int, ...]


def _area_of(checkpoint: str) -> str:
    if checkpoint not in GYM_AREAS:
        raise KeyError("nao e um ginasio: %s" % checkpoint)
    return GYM_AREAS[checkpoint]


def stages_of(checkpoint: str, trainers) -> list[Stage]:
    """A sala inteira, pela ordem em que se luta, com o lider no fim."""
    area = _area_of(checkpoint)
    inside = [t for t in trainers if t.area == area]
    others = [t for t in inside if t.name not in LEADERS]
    leader = [t for t in inside if t.name in LEADERS]
    return [Stage(t.name, t.levels) for t in others + leader]


def leader_only(checkpoint: str, trainers) -> list[Stage]:
    """So o lider -- o que o modelo contava antes, para comparar."""
    return stages_of(checkpoint, trainers)[-1:]


def mon_count(stages) -> int:
    return sum(len(stage.levels) for stage in stages)


def gauntlet(checkpoint: str, trainers) -> list[int]:
    """A fila achatada em niveis, um por mon, pela ordem em que aparecem."""
    return [level for stage in stages_of(checkpoint, trainers)
            for level in stage.levels]
