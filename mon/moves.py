"""Moves de Gen 3, com os filtros de inclusao do GRUPOS.md.

Duas armadilhas de dados no veekun, ambas por ele guardar valores MODERNOS:

1. `damage_class` e a classificacao Gen 4+, por move. Em Gen 3 o split
   fisico/especial e **por tipo**.
2. `power` e `pp` sao os valores atuais. 90 dos 354 moves de Gen 3 mudaram
   depois -- o Giga Drain era 60 BP / 5 PP, nao 75 / 10. O valor de Gen 3
   vem do `move_changelog`: e o da mudanca mais antiga posterior a Gen 3.
"""

from dataclasses import dataclass

from mon.damage import HITS_TWO_TO_FIVE

PHYSICAL_TYPES = frozenset({
    "NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG",
    "GHOST", "STEEL",
})


# Exclusoes decididas em GRUPOS.md
_OHKO = {"fissure", "guillotine", "horn-drill", "sheer-cold"}                 # A1
_SETUP = {                                                                    # A2
    "acid-armor", "agility", "amnesia", "barrier", "bulk-up", "calm-mind",
    "charge", "cosmic-power", "defense-curl", "double-team", "dragon-dance",
    "growth", "harden", "howl", "iron-defense", "meditate", "minimize",
    "sharpen", "swords-dance", "tail-glow", "withdraw",
}
_SELF_KO = {"self-destruct", "explosion", "perish-song"}                      # B3
_CONDITIONAL = {                                                              # B1, B1b
    "counter", "mirror-coat", "reversal", "flail", "bide", "endeavor",
    "spit-up", "beat-up", "present", "psywave",
    # O BP do hidden-power depende de IVs que nao se leem antes da run; o
    # veekun guarda 1 como placeholder e um BP fixo seria inventado.
    "hidden-power",
}
EXCLUDED = _OHKO | _SETUP | _SELF_KO | _CONDITIONAL

# Moves cujo dano nao vem do BP (GRUPOS.md B1). O segundo valor e o parametro:
# "level" ignora-o, "fixed" e o dano, "fraction" e a percentagem do HP atual.
SPECIAL_DAMAGE = {
    "seismic-toss": ("level", 0),
    "night-shade": ("level", 0),
    "dragon-rage": ("fixed", 40),
    "sonic-boom": ("fixed", 20),
    "super-fang": ("fraction", 50),
}

# Status incluidos porque causam dano (GRUPOS.md B2, B2b)
DAMAGING_STATUS = {
    "will-o-wisp", "toxic", "poison-powder", "poison-gas", "leech-seed",
    "nightmare", "curse", "spikes",
}

# BP efetivo dos moves cujo poder nao esta na tabela (GRUPOS.md B1)
EFFECTIVE_POWER = {
    "low-kick": 56,      # media do peso sobre os 386 mons de Gen 3
    "magnitude": 71,     # valor esperado das 7 magnitudes
    "return": 102,       # assume amizade maxima
    "frustration": 40,   # assumido a partir da saida do lab
    # O triple-kick escala 10/20/30 pelos tres golpes, 60 no total. O veekun
    # guarda 10, que e so o primeiro. 20 x 3 golpes da o mesmo total.
    "triple-kick": 20,
}


@dataclass(frozen=True)
class Move:
    name: str
    type: str
    power: int
    pp: int = 0
    drain: int = 0      # % do dano que cura o atacante
    kind: str = "power"
    hits: tuple = (1, 1)   # golpes por turno (minimo, maximo)

    @property
    def is_physical(self) -> bool:
        return self.type in PHYSICAL_TYPES

    @property
    def hit_chances(self) -> dict:
        """Distribuicao dos golpes por turno, para o `damage.py`."""
        if self.hits == (2, 5):
            return HITS_TWO_TO_FIVE
        return {self.hits[0]: 1.0}


def gen_3_value(current, history, field: str):
    """O valor de um campo em Gen 3, nao o atual.

    `history` sao pares (geracao em que mudou, campos com o valor de antes).
    A mudanca mais antiga posterior a Gen 3 guarda o valor que vigorava em
    Gen 3; se nunca mudou, o atual serve.
    """
    posteriores = sorted((gen, fields) for gen, fields in history
                         if gen > 3 and field in fields)
    return posteriores[0][1][field] if posteriores else current


def build_moves(moves, types, changelog=None, drain=None,
                hits=None) -> list[Move]:
    """Cruza as tabelas do veekun numa lista de moves utilizaveis."""
    changelog = changelog or {}
    drain = drain or {}
    hits = hits or {}
    type_name = {row["id"]: row["identifier"].upper() for row in types}
    built = []
    for row in moves:
        if row["identifier"] in EXCLUDED:
            continue
        history = changelog.get(row["identifier"], [])
        row = dict(row,
                   power=gen_3_value(row["power"], history, "power"),
                   pp=gen_3_value(row.get("pp", "0"), history, "pp"))
        power, kind = _damage_of(row)
        if kind == "status" and row["identifier"] not in DAMAGING_STATUS:
            continue
        built.append(Move(name=row["identifier"],
                          type=type_name[row["type_id"]],
                          power=power, pp=int(row["pp"] or 0),
                          drain=drain.get(row["identifier"], 0), kind=kind,
                          hits=hits.get(row["identifier"], (1, 1))))
    return built


def _damage_of(row) -> tuple[int, str]:
    """Como e que este move causa dano: quanto, e de que maneira."""
    name = row["identifier"]
    if name in SPECIAL_DAMAGE:
        kind, parameter = SPECIAL_DAMAGE[name]
        return parameter, kind
    if name in EFFECTIVE_POWER:
        return EFFECTIVE_POWER[name], "power"
    if row["power"]:
        return int(row["power"]), "power"
    return 0, "status"
