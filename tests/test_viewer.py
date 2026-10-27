import json

from mon.viewer import PLACEHOLDER, build_html


def test_the_payload_lands_where_the_placeholder_was():
    template = "<title>x</title><script>const DATA=" + PLACEHOLDER + ";</script>"
    page = build_html(template, {"ok": True})
    assert PLACEHOLDER not in page
    assert '{"ok":true}' in page


def test_a_template_without_a_placeholder_is_an_error():
    try:
        build_html("<title>x</title>", {})
    except ValueError:
        return
    raise AssertionError("sem placeholder os dados nao entram e a pagina mente")


def test_the_payload_survives_html_escaping():
    # Um "</script>" dentro dos dados fecharia o bloco e partia a pagina.
    page = build_html("<script>const DATA=" + PLACEHOLDER + ";</script>",
                      {"nome": "</script><b>"})
    assert "</script><b>" not in page.replace("</script>", "", 1)
    assert json.loads(page.split("const DATA=")[1].rsplit(";</script>", 1)[0]
                      .replace("\u003c", "<"))["nome"] == "</script><b>"


def test_the_engine_is_inlined_without_module_syntax():
    # Inline numa pagina, `export` e um erro de sintaxe que mata o script
    # todo em silencio.
    from mon.viewer import ENGINE_MARK
    template = "<script>" + ENGINE_MARK + "\nconst D=" + PLACEHOLDER + ";</script>"
    page = build_html(template, {}, "\nexport function f() { return 1; }\n")
    assert "export function" not in page
    assert "function f()" in page


def test_an_engine_without_a_slot_is_an_error():
    try:
        build_html("<script>const D=" + PLACEHOLDER + ";</script>", {}, "const x=1;")
    except ValueError:
        return
    raise AssertionError("o motor tinha de ir a lado nenhum sem falhar")


def test_the_page_is_built_into_docs_so_github_pages_serves_it():
    from mon.viewer import OUT, TEMPLATE, ENGINE
    assert OUT.parent.name == "docs" and OUT.name == "index.html"
    assert TEMPLATE.exists() and ENGINE.exists()
