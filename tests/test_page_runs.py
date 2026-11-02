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
      toggle: () => {}, add: () => {}, contains: () => false };
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
  return el ? el.children.length : -1;
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
    result = subprocess.run(["node", str(path)], capture_output=True,
                            text=True, timeout=600)
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
