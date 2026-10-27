"""O motor JS tem de dar o mesmo que o Python, numero a numero.

A pagina calcula movesets concretos ao vivo, e isso e um port de seis modulos
para JavaScript. Dois caminhos a responder ao mesmo foi como se apanhou o bug
da truncagem (CONTEXT.md 5); aqui a divergencia e verificada em vez de
esperada. O teste salta se o node nao estiver instalado.
"""

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from mon.export import PROFILES
from mon.moves import PHYSICAL_TYPES
from mon.pool import DefenderPool
from mon.score import score_variant
from mon.typechart import GEN_2_TO_5_INTERACTIONS
from mon.variants import variants
from mon.veekun import load_moves, load_species

ENGINE = Path(__file__).resolve().parent.parent / "viewer" / "engine.js"

CASES = [
    ("snorlax", ("physical", "hybrid", "bulky"), 19, 27, 18, ["surf"]),
    ("snorlax", ("physical", "hybrid", "bulky"), 19, 27, 18, ["giga-drain"]),
    ("snorlax", ("physical", "hybrid", "bulky"), 19, 27, 18,
     ["body-slam", "surf", "earthquake", "ice-beam"]),
    ("gengar", ("special", "spdef_tank", "fast"), 58, 15, 36,
     ["shadow-ball", "thunderbolt"]),
    ("onix", ("hybrid", "def_tank", "bulky"), 86, 5, 80,
     ["earthquake", "rock-slide", "body-slam", "surf"]),
]


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node nao esta instalado")
    species = load_species()
    moves = [m for m in load_moves() if m.kind == "power" and m.power]
    path = tmp_path_factory.mktemp("engine") / "fixture.json"
    path.write_text(json.dumps({
        "species": [[s.number, s.name, list(s.types), s.bst] for s in species],
        "profiles": PROFILES,
        "moves": [[m.name, m.type, m.power] for m in moves],
        "chart": GEN_2_TO_5_INTERACTIONS,
        "physical": sorted(PHYSICAL_TYPES),
    }))
    return path, {s.name: s for s in species}, {m.name: m for m in moves}


def test_the_browser_engine_matches_the_python_kernel(fixture):
    path, species, moves = fixture
    expected = []
    for name, profile, level, iv, their_level, names in CASES:
        attacker = next(v for v in variants(species[name], level, iv)
                        if v.profile == profile)
        pool = DefenderPool([v for other in species.values()
                             for v in variants(other, their_level, 31)])
        chosen = [moves[n] for n in names]
        cell = score_variant(attacker, chosen, pool, known=len(chosen))
        expected.append((cell.win, cell.hp_left))

    got = _run_node(path)
    for (win, hp), (js_win, js_hp), case in zip(expected, got, CASES):
        assert abs(win - js_win) < 1e-9, case
        assert abs(hp - js_hp) < 1e-9, case


def _run_node(fixture_path: Path):
    script = fixture_path.parent / "check.mjs"
    script.write_text(textwrap.dedent("""
        import fs from "node:fs";
        import { buildPool, makeChart, scoreMoveset, variantStats }
          from %(engine)s;
        const f = JSON.parse(fs.readFileSync(%(fixture)s, "utf8"));
        const eff = makeChart(f.chart);
        const physical = new Set(f.physical);
        const byName = new Map(f.moves.map(m =>
          ({ name: m[0], type: m[1], power: m[2] })).map(m => [m.name, m]));
        const byMon = new Map(f.species.map(s => [s[1], s]));
        const out = [];
        for (const [name, profile, level, iv, theirLevel, names] of %(cases)s) {
          const mon = byMon.get(name);
          const stats = variantStats(mon[3], profile, level, iv);
          const attacker = { ...stats, level, types: mon[2] };
          const pool = buildPool(f.species, f.profiles, theirLevel, eff);
          const r = scoreMoveset(attacker, names.map(n => byName.get(n)),
                                 pool, physical);
          out.push([r.win, r.hpLeft]);
        }
        console.log(JSON.stringify(out));
    """) % {
        "engine": json.dumps(ENGINE.as_uri()),
        "fixture": json.dumps(str(fixture_path)),
        "cases": json.dumps([[n, list(p), l, iv, tl, m]
                             for n, p, l, iv, tl, m in CASES]),
    })
    result = subprocess.run(["node", str(script)], capture_output=True,
                            text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
