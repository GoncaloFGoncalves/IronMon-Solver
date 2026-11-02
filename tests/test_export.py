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


def _block(root, rows, checkpoint="brock"):
    source = root / checkpoint
    source.mkdir(exist_ok=True)
    (source / "000.json").write_text(json.dumps(
        {"checkpoint": checkpoint, "level": 19, "opponent_level": 18,
         "rows": rows}))


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


def test_the_payload_carries_the_lethal_share(tmp_path):
    # 4b: a celula tem tres numeros. Sem o `risk` a pagina ordenava por
    # `hp_left`, que sobe quando o risco passa a ser binario.
    from mon.export import SCALE
    _block(tmp_path, [
        {"species": 1, "band": "20+", "profile": ["physical", "def_tank", "fast"],
         "win": 0.5, "hp_left": 0.25, "risk": 0.75, "known": 4},
    ])
    payload = build_payload(tmp_path, ["brock"])
    assert "risk" in payload
    risk = _decode(payload["risk"])
    index = cell_index(0, 0, 2, payload["profiles"].index(
        ["physical", "def_tank", "fast"]))
    assert risk[index] == round(0.75 * SCALE)


def test_a_block_without_risk_is_marked_missing(tmp_path):
    # Os blocos da v1 nao tem o campo. Em vez de os ler como risco zero --
    # que seria dizer "este mon nunca morre de um golpe" -- ficam MISSING.
    from mon.export import MISSING
    _block(tmp_path, [
        {"species": 1, "band": "20+", "profile": ["physical", "def_tank", "fast"],
         "win": 0.5, "hp_left": 0.25, "known": 4},
    ])
    payload = build_payload(tmp_path, ["brock"])
    risk = _decode(payload["risk"])
    index = cell_index(0, 0, 2, payload["profiles"].index(
        ["physical", "def_tank", "fast"]))
    assert risk[index] == MISSING


def test_the_three_arrays_stay_aligned_against_the_json_on_disk():
    # O risco so e util se sair na mesma celula que o win e o hp. Um array
    # desalinhado mostra o mon errado sem dar erro nenhum -- por isso
    # confere-se contra os ficheiros, nao contra o proprio empacotamento.
    import glob
    from pathlib import Path
    from mon.export import SCALE, build_payload, cell_index
    from mon.trainers import SPLITS
    root = Path(__file__).resolve().parent.parent / "data" / "camada0"
    if not glob.glob(str(root / "brock" / "*.json")):
        import pytest
        pytest.skip("a camada 0 nao esta calculada")

    payload = build_payload(root)
    win = _decode(payload["win"])
    hp = _decode(payload["hp"])
    risk = _decode(payload["risk"])
    bands = {name: i for i, name in enumerate(payload["bands"])}

    conferidas = 0
    for ci, checkpoint in enumerate(SPLITS):
        path = sorted((root / checkpoint).glob("*.json"))[0]
        block = json.loads(path.read_text())
        for row in block["rows"][::97]:
            index = cell_index(ci, row["species"] - 1, bands[row["band"]],
                               payload["profiles"].index(list(row["profile"])))
            assert win[index] == round(row["win"] * SCALE), (checkpoint, row)
            assert hp[index] == round(row["hp_left"] * SCALE), (checkpoint, row)
            assert risk[index] == round(row["risk"] * SCALE), (checkpoint, row)
            conferidas += 1
    assert conferidas > 100
