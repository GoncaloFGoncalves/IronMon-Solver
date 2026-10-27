"""Camada 0: o batch. `python -m mon.run`.

Ctrl+C a qualquer momento. Cada particao escreve ao acabar, e uma corrida
nova salta as que ja estao no disco -- o estado e o conjunto de ficheiros,
nao um ficheiro de progresso que se possa perder (CONTEXT.md 3.7).
"""

import argparse
import sys
import time
from pathlib import Path

from mon.batch import Partition, partitions, pending, run
from mon.dex import GEN_3
from mon.ivs import BANDS
from mon.levels import expected_levels, opponent_levels
from mon.learnset import moves_known_at
from mon.pool import DefenderPool
from mon.score import score_variant
from mon.tms import COMPATIBILITY, tms_available_at
from mon.trainers import SPLITS
from mon.vector import ko_table
from mon.variants import variants

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "camada0"
SPECIES_PER_BLOCK = 20
# O `checkpoints.py` e o `tms.py` usam o nome por extenso; os splits usam slug.
_CHECKPOINT_NAMES = {"brock": "Brock", "misty": "Misty", "surge": "Lt. Surge",
                     "erika": "Erika", "koga": "Koga", "sabrina": "Sabrina",
                     "blaine": "Blaine", "giovanni": "Giovanni",
                     "elite-4": "Elite 4"}


def all_partitions() -> list[Partition]:
    """A chave e `(checkpoint,)`: 9 checkpoints x blocos de especies.

    A curva de crescimento **nao** entra: o randomizer padroniza todos os mons
    para FLUCTUATING, logo ha uma curva e nao seis. A chave fica tupla porque
    e assim que uma dimensao nova se acrescenta sem invalidar o que ja esta
    escrito -- foi o que aconteceu a esta.
    """
    return partitions([(checkpoint,) for checkpoint in SPLITS],
                      list(range(0, len(GEN_3), SPECIES_PER_BLOCK)))


def status(out_dir=OUT_DIR) -> tuple[int, int]:
    todas = all_partitions()
    falta = len(pending(todas, out_dir))
    return len(todas) - falta, falta


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mon.run", description=__doc__)
    parser.add_argument("--checkpoint", help="correr so um checkpoint")
    parser.add_argument("--status", action="store_true",
                        help="dizer quanto falta e sair")
    parser.add_argument("--out", default=OUT_DIR, type=Path)
    args = parser.parse_args(argv)

    if args.status:
        feito, falta = status(args.out)
        print("%d particoes feitas, %d por fazer" % (feito, falta))
        return 0

    todas = all_partitions()
    if args.checkpoint:
        todas = [p for p in todas if p.key[0] == args.checkpoint]
        if not todas:
            parser.error("checkpoint desconhecido: %s" % args.checkpoint)

    falta = len(pending(todas, args.out))
    print("%d particoes por fazer. Ctrl+C para parar; retoma-se daqui." % falta)
    started = time.perf_counter()
    try:
        run(todas, _compute, args.out)
    except KeyboardInterrupt:
        feitas = falta - len(pending(todas, args.out))
        print("\nparado. %d particoes escritas em %.0f s. Corre outra vez "
              "para continuar." % (feitas, time.perf_counter() - started))
        return 130
    print("acabou em %.0f s." % (time.perf_counter() - started))
    return 0


def _compute(part: Partition) -> dict:
    """Uma particao: um bloco de especies contra o pool, num checkpoint."""
    from mon.veekun import load_moves, load_schedules, load_species, load_upside
    species = load_species()
    moves = [move for move in load_moves() if move.kind == "power" and move.power]
    upsides = load_upside()
    schedules = load_schedules()
    checkpoint, = part.key
    split = SPLITS.index(checkpoint)
    level = expected_levels()[split]
    # O adversario esta ao nivel que o mapa diz, nao ao meu: no Brock estou 8
    # niveis abaixo dele, e e dai que vem a dificuldade (3.3).
    their_level = opponent_levels()[split]
    table = ko_table()
    tms = len(tms_available_at(_CHECKPOINT_NAMES[checkpoint])) * COMPATIBILITY

    pool = DefenderPool([variant for other in species
                         for variant in variants(other, their_level, 31)])
    block = species[part.index:part.index + SPECIES_PER_BLOCK]

    rows = []
    for one in block:
        # Quantos moves o mon conhece: os do calendario mais os TMs que ja
        # apanhei, metade dos quais compativeis (3.5b).
        known = int(moves_known_at(schedules[one.number], level) + tms)
        for band, iv in BANDS:
            for attacker in variants(one, level, iv):
                cell = score_variant(attacker, moves, pool, known=known,
                                     upsides=upsides, table=table)
                rows.append({"species": one.number, "band": band,
                             "profile": list(attacker.profile),
                             "win": round(cell.win, 4),
                             "hp_left": round(cell.hp_left, 4),
                             "known": cell.known})
    return {"checkpoint": checkpoint, "level": level,
            "opponent_level": their_level, "rows": rows}


if __name__ == "__main__":
    sys.exit(main())
