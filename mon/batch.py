"""A camada 0 corre aos pedacos: 5 h hoje, nenhuma amanha, 20 depois.

Requisito, nao conveniencia (CONTEXT.md 3.7). As 37 h nao se correm de uma
vez, e isso impoe tres coisas ao desenho:

- o espaco e **particionado** por uma chave estavel e enumeravel -- checkpoint
  e especie do atacante;
- cada particao **escreve ao acabar**, e um arranque novo salta as que ja
  existem no disco;
- **nenhum estado atravessa particoes** -- o que ja esta calculado nao pode
  mudar de valor por se retomar mais tarde, ou a tabela fica inconsistente
  consigo mesma.

De graca vem o paralelismo por particao e poder recalcular um checkpoint so,
quando a tabela de niveis do 3.3 for calibrada em jogo.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Partition:
    """Uma fatia do trabalho. A chave e uma tupla porque as dimensoes mudam.

    Era `(checkpoint)`; passou a `(curva, checkpoint)` quando as 6 curvas de
    crescimento entraram. Como a chave e o caminho no disco, acrescentar uma
    dimensao nao invalida o que ja esta escrito -- vai para outra pasta.
    """

    key: tuple[str, ...]
    index: int

    def path(self, out_dir) -> Path:
        return Path(out_dir).joinpath(*self.key, f"{self.index:03d}.json")


def partitions(keys, indices) -> list[Partition]:
    """Todas as fatias, pela ordem em que convem corre-las.

    A chave primeiro: uma fatia inteira de chave e um resultado utilizavel
    por si (a tabela do Brock serve antes de o resto existir).
    """
    return [Partition(tuple(key), index)
            for key in keys for index in indices]


def pending(todas, out_dir) -> list[Partition]:
    """As que ainda nao estao escritas. E so isto que define o progresso."""
    return [part for part in todas if not part.path(out_dir).exists()]


def run(todas, compute, out_dir, keep_going: bool = False) -> list[Partition]:
    """Corre as que faltam. Devolve as que falharam.

    `compute` recebe uma `Partition` e devolve o que vai para JSON. Escreve-se
    para um ficheiro temporario e so depois se move: uma interrupcao a meio da
    escrita deixa a particao por fazer, nunca um resultado truncado que a
    corrida seguinte confundiria com trabalho feito.
    """
    failed = []
    for part in pending(todas, out_dir):
        try:
            result = compute(part)
        except KeyboardInterrupt:
            raise
        except Exception:
            if not keep_going:
                raise
            failed.append(part)
            continue
        destination = part.path(out_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(json.dumps(result))
        temporary.replace(destination)
    return failed
