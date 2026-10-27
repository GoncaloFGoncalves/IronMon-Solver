"""Secoes sem cura: quantas batalhas e preciso ganhar de seguida.

Dentro de uma dungeon nao ha cura, nao ha recarga de PP e nao se pode lutar
com mons selvagens. HP e PP passam a orcamentos que atravessam varias
batalhas (CONTEXT.md 3.6b), e o orcamento precisa de um denominador.

Conta-se **so o caminho obrigatorio**: os treinadores que e preciso vencer
para progredir. Todos os outros sao opcionais, e o trade-off de os evitar e
chegar ao checkpoint seguinte a um nivel mais baixo -- a tabela do 3.3 e o
teto, nao o que acontece numa run que evita tudo.

Os numeros sao estimativa de FRLG e estao por verificar em jogo (CONTEXT.md 6).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dungeon:
    name: str
    mandatory: int
    note: str


DUNGEONS = (
    Dungeon("pewter-gym", 1, "o lider; o treinador do ginasio contorna-se"),
    Dungeon("cerulean-gym", 1, "so a lider"),
    Dungeon("ss-anne", 1, "o rival na passarela; os marinheiros sao opcionais"),
    Dungeon("vermilion-gym", 1, "os interruptores estao nos lixos, nao nos treinadores"),
    Dungeon("rocket-hideout", 3, "o grunt da Lift Key, um grunt nos spinners, o Giovanni"),
    Dungeon("celadon-gym", 1, "so a lider"),
    Dungeon("pokemon-tower", 4, "o rival no 2F e os 3 grunts do 7F; o Marowak e a mais"),
    Dungeon("silph-co", 4, "o rival e o Giovanni no 11F, mais 2 forcados pelos warps"),
    Dungeon("fuchsia-gym", 1, "o labirinto evita-se quase todo"),
    Dungeon("saffron-gym", 3, "os warps forcam 2 treinadores antes da Sabrina"),
    Dungeon("cinnabar-gym", 1, "o quiz certo dispensa os treinadores"),
    Dungeon("viridian-gym", 2, "os spinners forcam 1 antes do Giovanni"),
)

_BY_NAME = {d.name: d for d in DUNGEONS}


def mandatory_battles(section: str) -> int:
    """Levanta KeyError numa secao desconhecida -- zero seria um orcamento falso."""
    return _BY_NAME[section].mandatory
