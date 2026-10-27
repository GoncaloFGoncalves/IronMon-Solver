"""Nivel esperado em cada split, calibrado contra runs reais.

**O randomizer padroniza a curva de crescimento de todos os mons para
FLUCTUATING.** Nao ha 6 curvas para simular -- ha uma. A dimensao existia no
modelo e nao existe no jogo.

Os adversarios sao randomizados, logo o exp yield de cada um e um sorteio do
pool: usa-se o valor esperado, em valores de Gen 3. A banda sai de os mons do
treinador poderem vir pre-evoluidos (yield medio 136) ou ja evoluidos (173) --
e e isso que explica a diferenca entre o nivel tipico e o maximo.

Calibracao: as duas observacoes de runs reais -- "no Brock ronda 18-19" e "21
e o maximo com mons ja evoluidos" -- saem do modelo **sem nada ajustado**. Ha
teste. Foi isso que tambem fixou o conjunto de treinadores: as runs reais
lutam com os das areas da rota, nao so com os inevitaveis.
"""

from mon.exp import STANDARD_CURVE, exp_from_defeating, level_at, thresholds
from mon.firered import load_species_info
from mon.trainers import LEADERS, SPLITS, load_trainers, split_of
from mon.veekun import load_table

START_LEVEL = 5          # o mon do laboratorio


def _yields() -> tuple[float, float]:
    """(media do pool, media so das especies que nao tem pre-evolucao)."""
    info = load_species_info()
    species = {row["identifier"]: row for row in load_table("pokemon_species")}
    evolved = {row["evolves_from_species_id"]
               for row in load_table("pokemon_species")
               if row["evolves_from_species_id"]}
    everything, finals = [], []
    for name, (value, _) in info.items():
        everything.append(value)
        row = species.get(name)
        if row is not None and row["id"] not in evolved:
            finals.append(value)
    return sum(everything) / len(everything), sum(finals) / len(finals)


MEAN_EXP_YIELD, FULLY_EVOLVED_EXP_YIELD = _yields()


def expected_levels(base_exp: float = None, start_level: int = START_LEVEL,
                    trainers=None, curve: str = STANDARD_CURVE) -> tuple[int, ...]:
    """Nivel a chegar a cada um dos 9 checkpoints, pela ordem dos `SPLITS`.

    O EXP do lider conta para o split **seguinte**: nao se paga por se chegar
    a si proprio.
    """
    base_exp = MEAN_EXP_YIELD if base_exp is None else base_exp
    gained = _exp_by_split(base_exp, load_trainers() if trainers is None
                           else trainers)
    experience = thresholds(curve)[start_level]
    levels = []
    for split in SPLITS:
        experience += gained[split]
        levels.append(level_at(curve, experience))
    return tuple(levels)


def level_band(**kwargs) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """(nivel tipico, nivel maximo) por split.

    O maximo e com o treinador a trazer mons ja evoluidos, que dao mais EXP.
    E a banda que se ve nas runs: 18-19 tipico e 21 no melhor caso, no Brock.
    """
    return (expected_levels(base_exp=MEAN_EXP_YIELD, **kwargs),
            expected_levels(base_exp=FULLY_EVOLVED_EXP_YIELD, **kwargs))


def opponent_levels(trainers=None) -> tuple[int, ...]:
    """Nivel do adversario em cada checkpoint: o do **lider**.

    Nada a ver com o nivel do jogador, e nao e a mediana da rota: o que
    importa e a parede. O Brock vem 18/18/18/18/21, logo 18 -- os bug
    catchers de nivel 9 do caminho nao baixam o que e preciso para o vencer.
    O Elite 4 nao esta no mapa; usa-se o que ha de mais alto no split, que e
    a revanche do rival antes da Victory Road.
    """
    trainers = load_trainers() if trainers is None else trainers
    out = []
    highest = 0
    for split in SPLITS:
        inside = [t for t in trainers if split_of(t) == split]
        leaders = [t for t in inside if t.name in LEADERS]
        party = sorted(level for t in (leaders or inside) for level in t.levels)
        if leaders:
            level = party[len(party) // 2]
        else:
            level = party[-1] if party else highest
        highest = max(highest, level)
        out.append(highest)
    return tuple(out)


def _exp_by_split(base_exp: float, trainers) -> dict[str, int]:
    """EXP ganho dentro de cada split, com o lider a contar para o seguinte."""
    gained = {split: 0 for split in SPLITS}
    for trainer in trainers:
        split = split_of(trainer)
        if split is None:
            continue
        index = SPLITS.index(split)
        if trainer.name in LEADERS:
            index = min(index + 1, len(SPLITS) - 1)
        for level in trainer.levels:
            gained[SPLITS[index]] += int(exp_from_defeating(base_exp, level))
    return gained
