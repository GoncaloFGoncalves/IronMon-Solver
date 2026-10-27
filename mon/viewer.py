"""Injeta a camada 0 e o motor no template do visualizador.

A pagina e um ficheiro so, com os dados la dentro: nao ha servidor, e abre-se
com duplo clique. O template e o `engine.js` ficam no repo e sao versionados;
o HTML construido e produto, como os JSON da camada 0.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "viewer" / "template.html"
ENGINE = ROOT / "viewer" / "engine.js"
# A pagina construida vai para `docs/`, que e de onde o GitHub Pages serve.
# E o unico produto que entra no git: o `data/` fica de fora, sao 35 MB.
OUT = ROOT / "docs" / "index.html"

PLACEHOLDER = "/*__DATA__*/null"
ENGINE_MARK = "/*__ENGINE__*/"
ESCAPED_LT = "\\u003c"


def build_html(template: str, payload: dict, engine: str = "") -> str:
    """Substitui os marcadores pelos dados e pelo motor.

    O `engine.js` e um modulo ES para poder ser corrido em node e comparado
    com o Python; inline numa pagina as palavras `export` sao erro de
    sintaxe, por isso caem aqui.
    """
    if PLACEHOLDER not in template:
        raise ValueError("o template nao tem %s" % PLACEHOLDER)
    if engine:
        if ENGINE_MARK not in template:
            raise ValueError("o template nao tem %s" % ENGINE_MARK)
        template = template.replace(
            ENGINE_MARK, engine.replace("\nexport ", "\n"))
    # Um `</script>` dentro dos dados fecharia o bloco. Escapar o `<` resolve
    # sem mexer no valor: o JSON le `\\u003c` como `<`.
    blob = json.dumps(payload, separators=(",", ":")).replace("<", ESCAPED_LT)
    return template.replace(PLACEHOLDER, blob)


def write(template_path, payload: dict, out_path, engine_path=None) -> Path:
    """Constroi a pagina e devolve o caminho onde ficou."""
    engine = (Path(engine_path).read_text(encoding="utf-8")
              if engine_path else "")
    out = Path(out_path)
    out.write_text(build_html(Path(template_path).read_text(encoding="utf-8"),
                              payload, engine), encoding="utf-8")
    return out


def main() -> int:
    """`python -m mon.viewer` -- reconstroi a pagina a partir do `data/camada0`."""
    from mon.export import build_payload, engine_data, species_table
    payload = build_payload(ROOT / "data" / "camada0")
    payload["species"] = species_table()
    payload.update(engine_data())
    if payload["missing"]:
        print("faltam %d celulas: corre `python -m mon.run` primeiro"
              % payload["missing"])
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write(TEMPLATE, payload, OUT, ENGINE)
    print("%s  %.2f MB" % (OUT, OUT.stat().st_size / 1e6))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
