"""Bandas de IV do atacante (CONTEXT.md 3.4).

O defensor assume-se perfeito; o atacante corre em tres bandas, porque na run
nao se leem os IVs de imediato e o que interessa e o intervalo.

A banda alta e **20+** e nao 25+: com 25+ os IVs 20 a 24 nao caiam em banda
nenhuma, e um mon real com IV 22 nao tinha linha na tabela.
"""

DEFENDER_IV = 31

BANDS = (("sub-10", 5), ("sub-20", 15), ("20+", 27))


def band_of(iv: int) -> str:
    """A banda a que um IV lido no tracker pertence."""
    if iv < 10:
        return "sub-10"
    if iv < 20:
        return "sub-20"
    return "20+"
