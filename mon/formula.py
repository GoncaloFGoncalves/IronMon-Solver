"""Formula de dano de Gen 3.

Produz o dano ANTES do roll aleatorio -- e esse valor que o damage.py consome
para calcular a probabilidade de KO.
"""


def damage_before_roll(level: int, power: int, attack: float, defense: float,
                       stab: bool, effectiveness: float) -> int:
    """Dano de um golpe, antes do roll de 85-100%."""
    damage = (2 * level // 5 + 2) * power * attack // defense // 50 + 2
    if stab:
        damage = int(damage * 1.5)
    return int(damage * effectiveness)
