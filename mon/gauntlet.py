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


# As areas do mapa de cada seccao do `dungeons.py`. Os ginasios estao aqui
# tambem, com a mesma grafia que o `GYM_AREAS` -- o mapa escreve "Fuschia" e
# "Vermillion", e nao se corrige: e a chave dos dados.
DUNGEON_AREAS = {
    "pewter-gym": "Pewter Gym",
    "cerulean-gym": "Cerulean Gym",
    "ss-anne": "S.S. Anne",
    "vermilion-gym": "Vermillion Gym",
    "rocket-hideout": "Rocket Hideout",
    "celadon-gym": "Celadon Gym",
    "pokemon-tower": "Pokemon Tower",
    "silph-co": "Silph Co",
    "fuchsia-gym": "Fuschia Gym",
    "saffron-gym": "Saffron Gym",
    "cinnabar-gym": "Cinnabar Gym",
    "viridian-gym": "Viridian Gym",
}


# O Elite 4 **e** uma dungeon -- a mais longa, cinco treinadores sem cura
# pelo meio -- mas e a unica que nao sai do mapa: o FRLGIronmonMap tem a
# Victory Road (45 mons, com o Pokemon Center do Plateau a seguir) e nao tem
# os cinco do Elite 4. Logo o numero e **dado**, nao derivado dos dados:
# 5 treinadores x 6 mons. Verificar em jogo (CONTEXT.md 5).
ELITE_FOUR_MONS = 30
ELITE_FOUR_BATTLES = 5


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


def checkpoint_mons(checkpoint: str, trainers) -> int:
    """Mons seguidos, sem cura, na seccao daquele checkpoint.

    E o denominador do relogio do status: o burn tira 1/8 do HP por turno e
    nao ha cura, logo o que importa nao e o checkpoint em si mas o tamanho da
    fila que ele obriga a fazer de uma vez.
    """
    from mon.trainers import SPLITS

    if checkpoint not in SPLITS:
        raise KeyError("checkpoint desconhecido: %s" % checkpoint)
    if checkpoint == "elite-4":
        return dungeon_mons("elite-4", trainers)
    return mon_count(stages_of(checkpoint, trainers))


def dungeon_mons(section: str, trainers) -> int:
    """Quantos mons seguidos, sem cura, naquela seccao.

    Num **ginasio** sao todos, por regra do desafio, e no **Elite 4** tambem.
    Fora disso os treinadores evitam-se, e o `dungeons.py` diz quantos
    embates a rota obriga -- mas nao **quais**, logo o numero de mons
    estima-se pelo tamanho medio de equipa daquela area. E estimativa, nos
    dois sentidos.
    """
    from mon.dungeons import mandatory_battles

    if section == "elite-4":
        return ELITE_FOUR_MONS
    if section not in DUNGEON_AREAS:
        raise KeyError("seccao desconhecida: %s" % section)
    area = DUNGEON_AREAS[section]
    inside = [t for t in trainers if t.area == area]
    if not inside:
        raise KeyError("o mapa nao tem treinadores em %s" % area)
    total = sum(len(t.levels) for t in inside)
    if area in set(GYM_AREAS.values()):
        return total
    mean = total / len(inside)
    return max(1, round(mandatory_battles(section) * mean))


def gauntlet(checkpoint: str, trainers) -> list[int]:
    """A fila achatada em niveis, um por mon, pela ordem em que aparecem."""
    return [level for stage in stages_of(checkpoint, trainers)
            for level in stage.levels]
