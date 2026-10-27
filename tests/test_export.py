import base64
import json

from mon.export import INDEX_ORDER, build_payload, cell_index


def test_the_index_is_a_pure_function_of_the_key():
    # A tabela viaja como dois arrays planos; a chave tem de dar sempre o
    # mesmo sitio ou o visualizador mostra o mon errado.
    assert cell_index(0, 0, 0, 0) == 0
    assert cell_index(0, 0, 0, 1) == 1
    assert cell_index(0, 0, 1, 0) == 27
    assert cell_index(0, 1, 0, 0) == 81
    assert cell_index(1, 0, 0, 0) == 386 * 3 * 27


def test_the_order_is_recorded_so_the_page_can_undo_it():
    assert INDEX_ORDER == ("checkpoint", "species", "band", "profile")


def test_the_payload_round_trips_a_known_cell(tmp_path):
    rows = [{"species": 1, "band": "sub-10", "profile": ["physical", "def_tank", "fast"],
             "win": 0.4305, "hp_left": 0.1784, "known": 10}]
    source = tmp_path / "brock"
    source.mkdir()
    (source / "000.json").write_text(json.dumps(
        {"checkpoint": "brock", "level": 19, "opponent_level": 18, "rows": rows}))

    payload = build_payload(tmp_path, checkpoints=["brock"])
    win = _decode(payload["win"])
    index = cell_index(0, 0, 0, payload["profiles"].index(
        ["physical", "def_tank", "fast"]))
    assert abs(win[index] / 10000 - 0.4305) < 1e-4


def test_an_unfilled_cell_is_not_silently_zero(tmp_path):
    source = tmp_path / "brock"
    source.mkdir()
    (source / "000.json").write_text(json.dumps(
        {"checkpoint": "brock", "level": 19, "opponent_level": 18, "rows": []}))
    payload = build_payload(tmp_path, checkpoints=["brock"])
    assert payload["missing"] > 0


def _decode(encoded):
    import array
    values = array.array("H")
    values.frombytes(base64.b64decode(encoded))
    return values


def test_the_engine_data_carries_what_the_browser_cannot_derive():
    from mon.export import engine_data
    data = engine_data()
    assert len(data["moves"]) > 150
    assert data["moves"][0][1].isupper(), "o tipo vem em maiusculas, como no chart"
    assert len(data["chart"]) == 17
    assert "NORMAL" in data["physical"] and "WATER" not in data["physical"]
    # Os stats derivam-se do BST, mas o IV de cada banda nao se deriva de nada.
    assert set(data["ivs"]) == {"sub-10", "sub-20", "20+"}
