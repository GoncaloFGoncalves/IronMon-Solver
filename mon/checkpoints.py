"""Os 9 splits da run: 8 ginasios mais a Elite 4 como um bloco.

Os niveis vanilha de FRLG sao a fonte; os do Kaizo derivam-se do level boost
de +50%. Guardar a derivacao em vez dos valores finais mantem o boost como
parametro -- se o ruleset mudar, muda um numero.

Estimativa calibrada contra o unico ponto observado em jogo: Brock = 20,
estimado 21, erro -1. Ver CONTEXT.md 3.3.
"""

from dataclasses import dataclass

LEVEL_BOOST = 1.5
FORCED_FULLY_EVOLVED_AT = 30


def kaizo_levels(vanilla_low: int, vanilla_high: int) -> tuple[int, int]:
    """A banda de niveis de um checkpoint depois do level boost do Kaizo."""
    return int(vanilla_low * LEVEL_BOOST), int(vanilla_high * LEVEL_BOOST)


@dataclass(frozen=True)
class Checkpoint:
    name: str
    vanilla_low: int
    vanilla_high: int

    @property
    def levels(self) -> tuple[int, int]:
        return kaizo_levels(self.vanilla_low, self.vanilla_high)

    @property
    def final_evolutions_only(self) -> bool:
        """Passado o forced evolution, o pool adversario encolhe."""
        return self.levels[0] >= FORCED_FULLY_EVOLVED_AT


CHECKPOINTS = (
    Checkpoint("Brock", 12, 14),
    Checkpoint("Misty", 18, 21),
    Checkpoint("Lt. Surge", 18, 24),
    Checkpoint("Erika", 24, 29),
    Checkpoint("Koga", 37, 43),
    Checkpoint("Sabrina", 37, 43),
    Checkpoint("Blaine", 40, 47),
    Checkpoint("Giovanni", 42, 50),
    Checkpoint("Elite 4", 51, 63),
)
