"""Quando cada TM fica disponivel ao longo da run.

Os moves dos TMs sao sorteados por run, mas *quais* os TMs que se apanham e
*onde* nao muda -- tal como o calendario de aprendizagem (learnset.py). Logo o
numero de TMs disponiveis num checkpoint e invariante.

Compatibilidade: 50/50 por mon (medido: 49.9%), logo metade dos disponiveis e
utilizavel em media. HMs ficam de fora.
"""

# (checkpoint a partir do qual estao disponiveis, TMs apanhados ate la)
TM_PICKUPS = (
    ("Brock", ("TM09", "TM46", "TM43")),                            # Mt. Moon, Route 25
    ("Misty", ("TM05",)),                                            # Route 4
    ("Lt. Surge", ("TM44",)),                                        # S.S. Anne
    ("Erika", ("TM12", "TM21", "TM40", "TM41", "TM01", "TM08")),     # Rocket Hideout, Silph
    ("Koga", ("TM11", "TM32", "TM47", "TM18")),                      # Safari Zone, Route 15
    ("Sabrina", ("TM17", "TM25", "TM48", "TM14", "TM22")),           # Power Plant, Mansion
    ("Blaine", ()),
    ("Giovanni", ("TM36",)),                                         # Rocket Warehouse
    ("Elite 4", ("TM02", "TM07", "TM37", "TM50")),                   # Victory Road
)

COMPATIBILITY = 0.5


def tms_available_at(checkpoint: str) -> tuple[str, ...]:
    """Todos os TMs ja apanhados quando chegas a este checkpoint."""
    collected: list[str] = []
    for name, picked_up in TM_PICKUPS:
        collected.extend(picked_up)
        if name == checkpoint:
            return tuple(collected)
    raise KeyError(checkpoint)
