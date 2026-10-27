"""Type charts por geracao.

O chart e um dado do jogo, nao uma constante global (CONTEXT.md 3.1). Gen 2-5
nao tem FAIRY, e STEEL resiste a DARK e a GHOST -- duas diferencas face ao
chart moderno que o coverage.py do legado tem errado (CONTEXT.md 5.7).

Cada linha lista so as interacoes diferentes de 1x; o resto e neutro.
"""

TYPES_GEN_2_TO_5 = (
    "NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG",
    "GHOST", "STEEL", "FIRE", "WATER", "GRASS", "ELECTRIC", "PSYCHIC",
    "ICE", "DRAGON", "DARK",
)

GEN_2_TO_5_INTERACTIONS = {
    "NORMAL":   {"ROCK": 0.5, "STEEL": 0.5, "GHOST": 0},
    "FIGHTING": {"NORMAL": 2, "ROCK": 2, "STEEL": 2, "ICE": 2, "DARK": 2,
                 "FLYING": 0.5, "POISON": 0.5, "BUG": 0.5, "PSYCHIC": 0.5, "GHOST": 0},
    "FLYING":   {"FIGHTING": 2, "BUG": 2, "GRASS": 2,
                 "ROCK": 0.5, "STEEL": 0.5, "ELECTRIC": 0.5},
    "POISON":   {"GRASS": 2,
                 "POISON": 0.5, "GROUND": 0.5, "ROCK": 0.5, "GHOST": 0.5, "STEEL": 0},
    "GROUND":   {"POISON": 2, "ROCK": 2, "STEEL": 2, "FIRE": 2, "ELECTRIC": 2,
                 "GRASS": 0.5, "BUG": 0.5, "FLYING": 0},
    "ROCK":     {"FLYING": 2, "BUG": 2, "FIRE": 2, "ICE": 2,
                 "FIGHTING": 0.5, "GROUND": 0.5, "STEEL": 0.5},
    "BUG":      {"GRASS": 2, "PSYCHIC": 2, "DARK": 2,
                 "FIGHTING": 0.5, "FLYING": 0.5, "POISON": 0.5, "GHOST": 0.5,
                 "STEEL": 0.5, "FIRE": 0.5},
    "GHOST":    {"PSYCHIC": 2, "GHOST": 2,
                 "DARK": 0.5, "STEEL": 0.5, "NORMAL": 0},
    "STEEL":    {"ROCK": 2, "ICE": 2,
                 "STEEL": 0.5, "FIRE": 0.5, "WATER": 0.5, "ELECTRIC": 0.5},
    "FIRE":     {"BUG": 2, "STEEL": 2, "GRASS": 2, "ICE": 2,
                 "ROCK": 0.5, "FIRE": 0.5, "WATER": 0.5, "DRAGON": 0.5},
    "WATER":    {"GROUND": 2, "ROCK": 2, "FIRE": 2,
                 "WATER": 0.5, "GRASS": 0.5, "DRAGON": 0.5},
    "GRASS":    {"GROUND": 2, "ROCK": 2, "WATER": 2,
                 "FLYING": 0.5, "POISON": 0.5, "BUG": 0.5, "STEEL": 0.5,
                 "FIRE": 0.5, "GRASS": 0.5, "DRAGON": 0.5},
    "ELECTRIC": {"FLYING": 2, "WATER": 2,
                 "GRASS": 0.5, "ELECTRIC": 0.5, "DRAGON": 0.5, "GROUND": 0},
    "PSYCHIC":  {"FIGHTING": 2, "POISON": 2,
                 "STEEL": 0.5, "PSYCHIC": 0.5, "DARK": 0},
    "ICE":      {"FLYING": 2, "GROUND": 2, "GRASS": 2, "DRAGON": 2,
                 "STEEL": 0.5, "FIRE": 0.5, "WATER": 0.5, "ICE": 0.5},
    "DRAGON":   {"DRAGON": 2, "STEEL": 0.5},
    "DARK":     {"GHOST": 2, "PSYCHIC": 2,
                 "FIGHTING": 0.5, "DARK": 0.5, "STEEL": 0.5},
}


class TypeChart:
    """Recebe as interacoes por injecao -- nao le ficheiros, nao imprime nada."""

    def __init__(self, interactions: dict[str, dict[str, float]]):
        self._interactions = interactions

    def effectiveness(self, attacking: str, defending: tuple[str, ...]) -> float:
        row = self._interactions[attacking]
        multiplier = 1.0
        for defender in defending:
            multiplier *= row.get(defender, 1)
        return multiplier


GEN_2_TO_5 = TypeChart(GEN_2_TO_5_INTERACTIONS)
