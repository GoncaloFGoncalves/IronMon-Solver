"""Formula de stats de Gen 3 (Ruby/Sapphire/Emerald/FireRed/LeafGreen)."""


def stat_at_level(base: float, level: int, iv: int, is_hp: bool) -> int:
    """Stat efetivo de um mon, assumindo EVs a zero e nature neutra.

    `base` aceita valores fracionarios porque o modelo de skew trabalha em
    fracoes exatas do BST (CONTEXT.md 3.2). Esta e a fronteira onde se
    converte para inteiro: no jogo um base stat e sempre inteiro.
    """
    common = (2 * round(base) + iv) * level // 100
    if is_hp:
        return common + level + 10
    return common + 5
