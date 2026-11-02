"""Secoes sem cura: quantas batalhas e preciso ganhar de seguida.

Dentro de uma dungeon nao ha cura, nao ha recarga de PP e nao se pode lutar
com mons selvagens. HP e PP passam a orcamentos que atravessam varias
batalhas (CONTEXT.md 3.6b), e o orcamento precisa de um denominador.

Conta-se **so o caminho obrigatorio**: os treinadores que e preciso vencer
para progredir. Fora dos ginasios os outros sao opcionais, e o trade-off de
os evitar e chegar ao checkpoint seguinte a um nivel mais baixo.

**Dentro de um ginasio nao ha opcionais**: o ruleset do desafio obriga a
lutar com todos. Nao e uma inferencia do mapa -- e uma regra, e por isso nao
depende de o treinador ser spinner ou estatico.

Os numeros sao estimativa de FRLG e estao por verificar em jogo (CONTEXT.md 6).

**Para os ginasios isto esta superado pelo `gauntlet.py`**, que conta mons em
vez de batalhas e poe a sala inteira antes do lider. O Brock aqui e 1; la sao
7 mons. Esta tabela fica para as seccoes que nao sao ginasios.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dungeon:
    name: str
    mandatory: int
    note: str


DUNGEONS = (
    Dungeon("pewter-gym", 2, "o Camper Liam e o Brock"),
    Dungeon("cerulean-gym", 3, "2 treinadores e a Misty"),
    Dungeon("ss-anne", 1, "o rival na passarela; os marinheiros sao opcionais"),
    Dungeon("vermilion-gym", 4, "3 treinadores e o Surge; os interruptores estao nos lixos"),
    Dungeon("rocket-hideout", 3, "o grunt da Lift Key, um grunt nos spinners, o Giovanni"),
    Dungeon("celadon-gym", 8, "7 treinadores e a Erika -- 24 mons seguidos"),
    Dungeon("pokemon-tower", 4, "o rival no 2F e os 3 grunts do 7F; o Marowak e a mais"),
    Dungeon("silph-co", 4, "o rival e o Giovanni no 11F, mais 2 forcados pelos warps"),
    Dungeon("fuchsia-gym", 7, "6 treinadores e o Koga; o labirinto nao dispensa ninguem"),
    Dungeon("saffron-gym", 8, "7 treinadores e a Sabrina"),
    Dungeon("cinnabar-gym", 8, "7 treinadores e o Blaine; o quiz nao dispensa ninguem"),
    Dungeon("viridian-gym", 9, "8 treinadores e o Giovanni -- 30 mons seguidos"),
)

_BY_NAME = {d.name: d for d in DUNGEONS}


def mandatory_battles(section: str) -> int:
    """Levanta KeyError numa secao desconhecida -- zero seria um orcamento falso."""
    return _BY_NAME[section].mandatory
