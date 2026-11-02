"""A pagina construida tem de **correr**, nao so compilar.

Um erro em runtime num painel rebenta o script todo e a pagina fica em
branco sem dizer nada. Aqui monta-se um DOM minimo em node, corre-se o
`init()` e conta-se o que ficou desenhado.
"""

import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

PAGE = Path(__file__).resolve().parent.parent / "docs" / "index.html"

SHIM = """
class El {
  constructor(tag) {
    this.tagName = (tag || "div").toUpperCase();
    this.children = []; this.dataset = {}; this.style = {}; this.classList = {
      toggle: () => {}, add: () => {}, remove: () => {},
      contains: () => false };
    this._text = ""; this.className = ""; this.hidden = false; this.options = [];
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() {
    return this._text + this.children.map(c => c.textContent).join("");
  }
  set innerHTML(v) { this._html = v; this.children = []; }
  get innerHTML() { return this._html || ""; }
  append(...kids) {
    for (const k of kids) this.children.push(typeof k === "string" ? new El("text") : k);
  }
  appendChild(k) { this.append(k); }
  setAttribute() {} getAttribute() { return null; }
  querySelectorAll() { return []; }
  querySelector() { return null; }
  closest() { return null; }
  addEventListener() {}
  get rows() { return this.children; }
}
const REG = new Map();
globalThis.Option = function (label, value) {
  const o = new El("option"); o._text = label; o.value = value; return o;
};
globalThis.document = {
  getElementById(id) {
    if (!REG.has(id)) REG.set(id, new El("div"));
    return REG.get(id);
  },
  createElement: (tag) => new El(tag),
  querySelectorAll: () => [],
  addEventListener: () => {},
};
globalThis.performance = { now: () => 0 };
globalThis.atob = (s) => Buffer.from(s, "base64").toString("binary");
globalThis.window = globalThis;
globalThis.__rows = (id) => {
  const el = REG.get(id);
  // Um elemento que ninguem tocou ainda nao tem linhas, que e zero -- nao e
  // um erro: e o estado antes de o painel calcular.
  return el ? el.children.length : 0;
};
"""


@pytest.fixture(scope="module")
def script():
    if shutil.which("node") is None:
        pytest.skip("node nao esta instalado")
    if not PAGE.exists():
        pytest.skip("a pagina nao esta construida")
    html = PAGE.read_text(encoding="utf-8")
    match = re.search(r"<script>(.*?)</script>", html, re.S)
    assert match, "a pagina nao tem o bloco de script"
    return match.group(1)


def _run(script, tail, tmp_path):
    path = tmp_path / "page.mjs"
    path.write_text(SHIM + "\n" + script + "\n" + tail, encoding="utf-8")
    # O node escreve UTF-8; sem isto o Windows decodifica em cp1252 e um
    # travessao na pagina chega aqui como caractere de substituicao.
    result = subprocess.run(["node", str(path)], capture_output=True,
                            text=True, encoding="utf-8", timeout=600)
    assert result.returncode == 0, result.stderr[-3000:]
    return json.loads(result.stdout)


def test_init_draws_every_panel(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        console.log(JSON.stringify({
          rank: __rows("rankBody"),
          run: __rows("runBody"),
          moveset: __rows("msBody"),
          breakpoints: __rows("bpBody"),
          worst: __rows("wmBody"),
          win: document.getElementById("msWin").textContent,
          risk: document.getElementById("msRisk").textContent,
        }));
    """), tmp_path)
    assert got["rank"] == 40, got
    assert got["run"] == 9, got
    assert got["moveset"] == 4, got
    # 17 tipos com pelo menos um move de dano.
    assert got["breakpoints"] == 17, got
    assert got["worst"] == 15, got
    assert re.fullmatch(r"0\.\d{4}|1\.0000", got["win"]), got["win"]
    assert re.fullmatch(r"0\.\d{4}|1\.0000", got["risk"]), got["risk"]


def test_the_wounded_slider_makes_more_types_lethal(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        const conta = () => document.getElementById("bpBody").children
          .filter(r => r.className !== "quiet").length;
        const cheio = conta();
        state.bpHp = 10;
        renderBreak();
        const ferido = conta();
        console.log(JSON.stringify({ cheio, ferido }));
    """), tmp_path)
    assert got["ferido"] > got["cheio"], got


def test_the_custom_panel_waits_for_the_button(script, tmp_path):
    # Os nove checkpoints custam ~0.43 s: nada corre sozinho.
    got = _run(script, textwrap.dedent("""
        init();
        const antes = __rows("cuBody");
        const aviso = document.getElementById("cuStale").textContent;
        renderCustom();
        console.log(JSON.stringify({
          antes, aviso, depois: __rows("cuBody"),
          limpo: document.getElementById("cuStale").textContent,
        }));
    """), tmp_path)
    assert got["antes"] == 0, got
    assert got["aviso"], "tem de avisar que ha mudancas por calcular"
    assert got["depois"] == 9, got
    assert got["limpo"] == "", got


def test_the_custom_panel_draws_the_whole_run(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        renderCustom();
        console.log(JSON.stringify({
          linhas: __rows("cuBody"),
          sliders: __rows("cuSliders"),
          orcamento: document.getElementById("cuBudget").textContent,
        }));
    """), tmp_path)
    assert got["linhas"] == 9, got
    assert got["sliders"] == 6, got
    assert "desalinhado" not in got["orcamento"], got["orcamento"]


def test_the_sliders_only_mark_stale(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        renderCustom();
        const depois = __rows("cuBody");
        state.custom.bases[1] += 10;
        fixBudget(1);
        markStale();
        console.log(JSON.stringify({
          depois, aviso: document.getElementById("cuStale").textContent,
          linhas: __rows("cuBody"),
        }));
    """), tmp_path)
    assert got["depois"] == 9
    assert got["aviso"], got
    # A tabela antiga fica no ecra, nao se apaga: so deixa de estar actual.
    assert got["linhas"] == 9, got


def test_the_sliders_always_preserve_the_bst(script, tmp_path):
    # O invariante do modelo: em Kaizo os stats redistribuem-se, nao se
    # inventam. Qualquer slider em qualquer extremo tem de somar o BST.
    got = _run(script, textwrap.dedent("""
        init();
        const bst = () => DATA.species[state.custom.s][3];
        const soma = () => state.custom.bases.reduce((a, b) => a + b, 0);
        const falhas = [];
        for (const sp of [142, 0, 150]) {
          state.custom.s = sp;
          state.custom.bases = null;
          customBases();
          for (let i = 0; i < 6; i++) {
            for (const v of [1, 50, 200, bst() - 5]) {
              state.custom.bases[i] = v;
              fixBudget(i);
              if (soma() !== bst()) falhas.push([sp, i, v, soma(), bst()]);
              if (Math.min(...state.custom.bases) < 1) falhas.push(["floor", sp, i, v]);
            }
          }
        }
        console.log(JSON.stringify({ falhas }));
    """), tmp_path)
    assert got["falhas"] == [], got["falhas"]


def test_the_presets_land_on_the_grid_profiles(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        const out = {};
        for (const name of ["hybrid", "physical", "special", "bulky", "fast"]) {
          loadPreset(name);
          out[name] = state.custom.bases.slice();
        }
        console.log(JSON.stringify(out));
    """), tmp_path)
    # Snorlax, BST 540: hibrido da 90 em tudo; fisico concentra em Atk.
    assert got["hybrid"] == [90, 90, 90, 90, 90, 90], got["hybrid"]
    assert got["physical"][1] == 135 and got["physical"][3] == 45, got["physical"]
    assert sum(got["bulky"]) == 540 and got["bulky"][0] > got["bulky"][5]


def test_the_ability_column_only_fills_when_one_is_chosen(script, tmp_path):
    got = _run(script, textwrap.dedent("""
        init();
        renderCustom();
        // A coluna da ability e a ultima; antes dela esta a dos mons.
        const linha = (cp) => document.getElementById("cuBody").children[cp];
        const ability = (cp) => linha(cp).children[6].textContent;
        const mons = (cp) => linha(cp).children[5].textContent;
        const sem = ability(0);
        state.custom.ability = "guts";
        renderCustom();
        console.log(JSON.stringify({
          sem, brock: ability(0), elite: ability(8),
          monsBrock: mons(0), monsElite: mons(8),
        }));
    """), tmp_path)
    assert got["sem"] == "\u2014", got
    # O rel\u00f3gio do status \u00e9 por checkpoint: 7 mons no Brock, 30 no Elite 4.
    # 30 mons s\u00e3o ~90 turnos de burn, logo ali o Guts n\u00e3o vale nada.
    assert got["monsBrock"] == "7" and got["monsElite"] == "30", got
    brock = float(got["brock"][1:])
    elite = 0.0 if got["elite"] == "\u2014" else float(got["elite"][1:])
    assert brock > 0.01, got
    assert elite < 0.001, got
    assert brock / max(elite, 1e-12) > 50, got


def test_the_sampling_stride_is_coprime_with_the_profile_count(script, tmp_path):
    # O pool esta ordenado por especie x perfil, com 27 perfis. Um passo que
    # divida 27 apanha sempre os mesmos perfis de cada especie: com passo 3 o
    # erro do `win` salta de 0.001 para 0.008. Com 7 ou 11 percorre a grelha.
    got = _run(script, textwrap.dedent("""
        init();
        const perfis = DATA.profiles.length;
        const vistos = new Set();
        const pool = customPool(0);
        for (let i = 0; i < pool.rows.length; i++) {
          vistos.add((i * CUSTOM_STRIDE) % perfis);
        }
        console.log(JSON.stringify({
          stride: CUSTOM_STRIDE, perfis, distintos: vistos.size,
          amostrados: pool.rows.length,
        }));
    """), tmp_path)
    assert got["perfis"] == 27
    # Coprimo: o passo percorre os 27 perfis, nao um subconjunto.
    assert got["distintos"] == 27, got
    import math
    assert math.gcd(got["stride"], got["perfis"]) == 1, got
