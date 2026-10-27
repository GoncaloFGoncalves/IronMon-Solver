import json

from mon.run import OUT_DIR, SPECIES_PER_BLOCK, all_partitions, status


def test_the_curve_is_not_a_dimension_because_the_randomizer_fixes_it():
    # Todos os mons sao FLUCTUATING: ha uma curva, nao seis.
    todas = all_partitions()
    assert {p.key for p in todas} >= {("brock",), ("elite-4",)}
    assert len({p.key for p in todas}) == 9


def test_no_species_is_left_out_or_repeated():
    blocos = sorted({p.index for p in all_partitions()})
    assert blocos[0] == 0
    assert len(blocos) * SPECIES_PER_BLOCK >= 386


def test_status_counts_what_is_on_disk(tmp_path):
    assert status(tmp_path) == (0, len(all_partitions()))
    part = all_partitions()[0]
    part.path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    part.path(tmp_path).write_text(json.dumps({}))
    feito, falta = status(tmp_path)
    assert feito == 1 and falta == len(all_partitions()) - 1


def test_the_default_output_lives_under_data():
    assert OUT_DIR.name == "camada0"
