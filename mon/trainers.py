"""Os treinadores do FRLGIronmonMap, por split do playthrough intencionado.

Os niveis do mapa **ja sao os do Kaizo**, nao os do vanilla: o Brock vem
18/18/18/18/21 e nao 12/14. Logo nao se aplica o `LEVEL_BOOST` por cima --
seria contar o boost duas vezes.

Um split e o conjunto de areas que se atravessa antes de um checkpoint, pela
ordem intencionada do jogo. Os treinadores opcionais de outras areas nao
contam: nao se vai la na rota.

O lider nao paga por se chegar a ele proprio -- o EXP do Brock conta para o
split seguinte.
"""

import re
from dataclasses import dataclass
from pathlib import Path
import urllib.request

URL = ("https://raw.githubusercontent.com/kelseyyoung/FRLGIronmonMap/main/"
       "src/data/trainers.ts")
CACHE = Path(__file__).resolve().parent.parent / "data" / "frlgmap" / "trainers.ts"

def slug(name: str) -> str:
    """O nome de um checkpoint como chave: "Lt. Surge" -> "surge"."""
    return (name.lower().replace("lt. ", "").replace(".", "")
            .replace(" ", "-"))


# Os 9 checkpoints do `checkpoints.py`, em chave. Ha teste de consistencia:
# tres modulos com tres grafias dos mesmos nomes e um bug a espera.
SPLITS = ("brock", "misty", "surge", "erika", "koga",
          "sabrina", "blaine", "giovanni", "elite-4")

LEADERS = frozenset({"Brock", "Misty", "Lt. Surge", "Erika", "Koga",
                     "Sabrina", "Blaine", "Giovanni"})

# A ordem intencionada de FRLG. O Rt 11 fica depois do Surge porque precisa
# do Cut; o Rocket Hideout depois da Erika porque a Silph Scope so serve para
# a Pokemon Tower, que vem a seguir.
AREA_SPLITS = {
    "Viridian Forest": "brock",
    "Viridian Rival": "brock",
    "Pewter Gym": "brock",

    "Route 03/Pre Mt. Moon": "misty",
    "Mt. Moon": "misty",
    "Rt 4/Post Mt Moon": "misty",
    "Rt 24/Nugget Bridge": "misty",
    "Cerulean Gym": "misty",

    "Rt 25": "surge",
    "Cerulean City": "surge",
    "Rt 6": "surge",
    "S.S. Anne": "surge",
    "Vermillion Gym": "surge",

    "Rt 11": "erika",
    "Rt9/Pre Rock Tunnel": "erika",
    "Rock Tunnel": "erika",
    "Rt10": "erika",
    "Rt 8": "erika",
    "Celadon Gym": "erika",

    "Rocket Hideout": "koga",
    "Pokemon Tower": "koga",
    "Rt12": "koga",
    "Rt13": "koga",
    "Rt14": "koga",
    "Rt15": "koga",
    "Fuschia City": "koga",
    "Fuschia Gym": "koga",

    "Silph Co": "sabrina",
    "Saffron Gym": "sabrina",

    "Cycling Road": "blaine",
    "Power Plant": "blaine",
    "Rt19": "blaine",
    "Seafoam Islands": "blaine",
    "Rt 20": "blaine",
    "Pokemon Mansion": "blaine",
    "Rt 21": "blaine",
    "Cinnabar Gym": "blaine",

    "Viridian Gym": "giovanni",

    "Victory Road": "elite-4",

    # Opcionais: estao no mapa mas nao na rota.
    "Fighting Dojo": None,
}

# O "Rival (Second)" esta na area do Rt 22 mas e a revanche imediatamente
# antes da Victory Road -- os niveis (68-80) passam o Giovanni.
_LATE_RIVAL = "Rival (Second)"

_AREA = re.compile(r"^\s*//\s*(.+?)\s*$")
_NAME = re.compile(r'^\s*name: "(.+?)",')
_LEVELS = re.compile(r"^\s*pokemonLevels: \[(.*?)\],")
_FLAG = re.compile(r"^\s*(spinner|walker): true,")
_FLOOR = re.compile(r"^(\d+F|B\d+F?|1B|Main Floor|Lower Floor|Deck|Upper Level"
                    r"|Top 6 trainers|Lower part of Cycling Road)$")


@dataclass(frozen=True)
class Trainer:
    area: str
    name: str
    levels: tuple[int, ...]
    spinner: bool = False   # roda no lugar: nao se contorna de forma fiavel
    walker: bool = False    # anda de um lado para o outro: o mesmo


def parse_trainers(text: str) -> list[Trainer]:
    """Le o `trainers.ts`. Os comentarios delimitam as areas."""
    area = None
    rows: list[list] = []
    for line in text.splitlines():
        comment = _AREA.match(line)
        if comment:
            label = comment.group(1)
            # Os "TODO" e os pisos nao sao areas novas.
            if not label.startswith("TODO") and not _FLOOR.match(label):
                area = label
            continue
        name = _NAME.match(line)
        if name:
            rows.append([area, name.group(1), None, set()])
            continue
        levels = _LEVELS.match(line)
        if levels and rows:
            rows[-1][2] = tuple(int(value) for value in levels.group(1).split(","))
            continue
        flag = _FLAG.match(line)
        if flag and rows:
            rows[-1][3].add(flag.group(1))
    return [Trainer(area, name, parties,
                    spinner="spinner" in flags, walker="walker" in flags)
            for area, name, parties, flags in rows if parties is not None]


def load_trainers() -> list[Trainer]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE.exists():
        request = urllib.request.Request(URL, headers={"User-Agent": "mon"})
        CACHE.write_text(urllib.request.urlopen(request).read().decode("utf-8"),
                         encoding="utf-8")
    return parse_trainers(CACHE.read_text(encoding="utf-8"))


def split_of(trainer: Trainer) -> str | None:
    if trainer.name == _LATE_RIVAL:
        return "elite-4"
    return AREA_SPLITS.get(trainer.area)


def trainers_before(split: str, trainers) -> list[Trainer]:
    """Tudo o que se vence antes do checkpoint, o proprio lider excluido."""
    limit = SPLITS.index(split)
    return [trainer for trainer in trainers
            if (found := split_of(trainer)) is not None
            and SPLITS.index(found) <= limit
            and not (SPLITS.index(found) == limit and trainer.name in LEADERS)]


def unavoidable(trainers) -> list[Trainer]:
    """Os treinadores que a rota obriga, e so esses.

    Aproximacao, nos dois sentidos: um spinner com bom temporizacao evita-se,
    e um treinador estatico num corredor de um tile nao se evita. O mapa nao
    marca "obrigatorio", marca **movimento**, e e o melhor sinal que tem.
    """
    return [trainer for trainer in trainers
            if trainer.spinner or trainer.walker
            or trainer.name in LEADERS or trainer.name.startswith("Rival")]
