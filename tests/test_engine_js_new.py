"""Os caminhos novos do motor JS: breakpoints, piores matchups, risco.

O `test_engine_js.py` cobre a celula. Estes tres sao codigo novo portado e
precisam do mesmo tratamento: dois caminhos a responder ao mesmo ja apanharam
tres bugs neste projeto (CONTEXT.md 4).
"""

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from mon.breakpoints import Threat, breakpoint_of, chain
from mon.export import PROFILES
from mon.matchups import worst_matchups
from mon.moves import PHYSICAL_TYPES
from mon.pool import DefenderPool
from mon.score import score_variant
from mon.typechart import GEN_2_TO_5_INTERACTIONS
from mon.variants import variants
from mon.veekun import load_moves, load_species

ENGINE = Path(__file__).resolve().parent.parent / "viewer" / "engine.js"
LEVEL, IV, THEIR_LEVEL = 70, 27, 56
PROFILE = ("physical", "def_tank", "fast")
THREAT = Threat(attack=95, special_attack=95, stab=1.0)
HURT = 12


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node nao esta instalado")
    species = load_species()
    moves = [m for m in load_moves() if m.kind == "power" and m.power]
    path = tmp_path_factory.mktemp("engine2") / "fixture.json"
    path.write_text(json.dumps({
        "species": [[s.number, s.name, list(s.types), s.bst] for s in species],
        "profiles": PROFILES,
        "moves": [[m.name, m.type, m.power] for m in moves],
        "chart": GEN_2_TO_5_INTERACTIONS,
        "physical": sorted(PHYSICAL_TYPES),
    }))
    gyarados = [s for s in species if s.name == "gyarados"][0]
    attacker = next(v for v in variants(gyarados, LEVEL, IV)
                    if v.profile == PROFILE)
    pool = DefenderPool([v for other in species
                         for v in variants(other, THEIR_LEVEL, 31)])
    return path, species, moves, attacker, pool


def test_the_breakpoint_chain_matches(world):
    path, _, moves, attacker, _ = world
    got = _run(path, "chain")
    for kind in ("ELECTRIC", "ROCK", "GRASS", "GROUND"):
        mine = chain(attacker, moves, kind, THREAT, THEIR_LEVEL)
        theirs = got[kind]
        assert [r.move for r in mine] == [r["move"] for r in theirs], kind
        assert [r.damage for r in mine] == [r["damage"] for r in theirs], kind
        for a, b in zip(mine, theirs):
            assert abs(a.ohko - b["ohko"]) < 1e-9, (kind, a.move)
            assert abs(a.two - b["two"]) < 1e-9, (kind, a.move)


def test_the_wounded_chain_matches(world):
    path, _, moves, attacker, _ = world
    got = _run(path, "hurt")
    mine = chain(attacker, moves, "PSYCHIC", THREAT, THEIR_LEVEL, hp=HURT)
    assert [r.move for r in mine] == [r["move"] for r in got["PSYCHIC"]]
    for a, b in zip(mine, got["PSYCHIC"]):
        assert abs(a.ohko - b["ohko"]) < 1e-9, a.move
    # E o ponto da feature: ferido, mata muito mais do que a HP cheio.
    cheio = chain(attacker, moves, "PSYCHIC", THREAT, THEIR_LEVEL)
    assert sum(r.ohko == 1.0 for r in mine) > sum(r.ohko == 1.0 for r in cheio)


def test_the_breakpoint_pair_matches(world):
    path, _, moves, attacker, _ = world
    got = _run(path, "breakpoint")
    for kind in ("ELECTRIC", "ROCK"):
        last, first = breakpoint_of(chain(attacker, moves, kind, THREAT,
                                          THEIR_LEVEL))
        assert (last.move if last else None) == got[kind][0], kind
        assert (first.move if first else None) == got[kind][1], kind


def test_the_worst_matchups_match(world):
    path, _, moves, attacker, pool = world
    chosen = [m for m in moves
              if m.name in ("waterfall", "earthquake", "return")]
    mine = worst_matchups(attacker, chosen, pool, known=len(chosen), limit=10,
                          threat_moves=moves)
    got = _run(path, "worst")
    assert len(got) == len(mine)
    for a, b in zip(mine, got):
        assert a.defender.species.name == b["name"], (a.defender.species.name,
                                                      b["name"])
        assert abs(a.win - b["win"]) < 1e-9, a.defender.species.name


def test_the_risk_from_a_concrete_moveset_matches(world):
    path, _, moves, attacker, pool = world
    chosen = [m for m in moves
              if m.name in ("waterfall", "earthquake", "return")]
    cell = score_variant(attacker, chosen, pool, known=len(chosen),
                         threat_moves=moves)
    got = _run(path, "risk")
    assert abs(cell.risk - got) < 1e-9


def _run(fixture_path: Path, what: str):
    script = fixture_path.parent / ("check_%s.mjs" % what)
    script.write_text(textwrap.dedent("""
        import fs from "node:fs";
        import { breakpointOf, buildPool, chain, makeChart, scoreMoveset,
                 variantStats, worstMatchups } from %(engine)s;
        const f = JSON.parse(fs.readFileSync(%(fixture)s, "utf8"));
        const eff = makeChart(f.chart);
        const physical = new Set(f.physical);
        const all = f.moves.map(m => ({ name: m[0], type: m[1], power: m[2] }));
        const byName = new Map(all.map(m => [m.name, m]));
        const mon = f.species.find(s => s[1] === "gyarados");
        const stats = variantStats(mon[3], %(profile)s, %(level)d, %(iv)d);
        const attacker = { ...stats, level: %(level)d, types: mon[2] };
        const threat = { attack: 95, specialAttack: 95, stab: 1.0 };
        const pool = buildPool(f.species, f.profiles, %(their)d, eff);
        const mine = ["waterfall", "earthquake", "return"].map(n => byName.get(n));
        const what = %(what)s;
        let out;
        if (what === "chain") {
          out = {};
          for (const k of ["ELECTRIC", "ROCK", "GRASS", "GROUND"])
            out[k] = chain(attacker, all, k, threat, %(their)d, eff,
                           physical).rungs;
        } else if (what === "hurt") {
          out = { PSYCHIC: chain(attacker, all, "PSYCHIC", threat, %(their)d,
                                 eff, physical, %(hurt)d).rungs };
        } else if (what === "breakpoint") {
          out = {};
          for (const k of ["ELECTRIC", "ROCK"]) {
            const [a, b] = breakpointOf(chain(attacker, all, k, threat,
                                              %(their)d, eff, physical).rungs);
            out[k] = [a ? a.move : null, b ? b.move : null];
          }
        } else if (what === "worst") {
          out = worstMatchups(attacker, mine, pool, physical, all, 10)
            .map(r => ({ name: f.species[Math.floor(r.index / f.profiles.length)][1],
                         win: r.win }));
        } else {
          out = scoreMoveset(attacker, mine, pool, physical, all).risk;
        }
        console.log(JSON.stringify(out));
    """) % {
        "engine": json.dumps(ENGINE.as_uri()),
        "fixture": json.dumps(str(fixture_path)),
        "profile": json.dumps(list(PROFILE)),
        "level": LEVEL, "iv": IV, "their": THEIR_LEVEL, "hurt": HURT,
        "what": json.dumps(what),
    })
    result = subprocess.run(["node", str(script)], capture_output=True,
                            text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
