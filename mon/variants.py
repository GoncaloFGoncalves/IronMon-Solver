"""De especie + perfil + nivel para numeros de combate.

E a cola entre o modelo de skew (3.2), a formula de stat de Gen 3 e o motor
de score. Uma variante e **uma linha da tabela**: a especie que apanhei, o
perfil de stats que me saiu, a banda de IV e o nivel do checkpoint.
"""

from dataclasses import dataclass

from mon.dex import Species
from mon.formula import damage_before_roll
from mon.skew import profiles
from mon.stats import stat_at_level
from mon.typechart import GEN_2_TO_5


@dataclass(frozen=True)
class Variant:
    species: Species
    profile: tuple[str, str, str]   # (ofensivo, defensivo, tempo)
    level: int
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    bases: tuple[float, ...]        # base stats antes da formula

    @property
    def types(self) -> tuple[str, ...]:
        return self.species.types


def variants(species: Species, level: int, iv: int) -> list[Variant]:
    """As 27 variantes de uma especie, ja em stats efetivos."""
    out = []
    for profile in profiles(species.bst):
        bases = profile.as_tuple()
        hp, attack, defense, special_attack, special_defense, speed = (
            stat_at_level(base, level, iv, is_hp=index == 0)
            for index, base in enumerate(bases))
        out.append(Variant(
            species=species,
            profile=(profile.offensive, profile.defensive, profile.tempo),
            level=level, hp=hp, attack=attack, defense=defense,
            special_attack=special_attack, special_defense=special_defense,
            speed=speed, bases=bases))
    return out


def neutral_damage(attacker: Variant, defender: Variant, power: int,
                   physical: bool) -> int:
    """Um golpe sem tipo: nem STAB nem efetividade.

    E o que se assume do adversario, cujos moves sao randomizados e nao
    constam do mapa. Separado do `attack_damage` de proposito -- nao e um
    move de um tipo desconhecido, e a ausencia de informacao de tipo.
    """
    return damage_before_roll(
        level=attacker.level, power=power,
        attack=attacker.attack if physical else attacker.special_attack,
        defense=defender.defense if physical else defender.special_defense,
        stab=False, effectiveness=1.0)


def attack_damage(attacker: Variant, defender: Variant, power: int,
                  move_type: str, physical: bool = None) -> int:
    """Dano antes do roll de um golpe. Zero quando o tipo nao afeta.

    A categoria fisico/especial sai do **tipo do move**, nunca de um campo
    por move: em Gen 3 a divisao e por tipo (ver `moves.PHYSICAL_TYPES`).
    """
    from mon.moves import PHYSICAL_TYPES
    if physical is None:
        physical = move_type in PHYSICAL_TYPES
    effectiveness = GEN_2_TO_5.effectiveness(move_type, defender.types)
    if effectiveness == 0:
        return 0
    return damage_before_roll(
        level=attacker.level, power=power,
        attack=attacker.attack if physical else attacker.special_attack,
        defense=defender.defense if physical else defender.special_defense,
        stab=move_type in attacker.types, effectiveness=effectiveness)
