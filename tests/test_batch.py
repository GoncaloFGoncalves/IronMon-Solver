import json

import pytest

from mon.batch import Partition, partitions, pending, run


def test_the_space_is_partitioned_by_a_key_of_any_depth():
    # A chave e uma tupla porque as dimensoes mudaram: era (checkpoint), e
    # passou a (curva, checkpoint) quando as 6 curvas entraram.
    todas = partitions([("brock",), ("misty",)], [1, 4, 7])
    assert len(todas) == 6
    assert Partition(("brock",), 4) in todas

    fundo = partitions([("slow", "brock"), ("fast", "brock")], [1])
    assert Partition(("slow", "brock"), 1) in fundo


def test_a_finished_partition_is_written_and_skipped_on_the_next_run(tmp_path):
    chamadas = []

    def compute(part):
        chamadas.append(part)
        return {"score": part.index * 2}

    todas = partitions([("brock",)], [1, 4])
    run(todas, compute, tmp_path)
    assert len(chamadas) == 2

    run(todas, compute, tmp_path)
    assert len(chamadas) == 2, "a segunda corrida nao recalcula nada"


def test_the_results_survive_on_disk(tmp_path):
    run(partitions([("medium", "brock")], [4]), lambda p: {"score": 8}, tmp_path)
    ficheiro = tmp_path / "medium" / "brock" / "004.json"
    assert json.loads(ficheiro.read_text())["score"] == 8


def test_an_interrupted_run_resumes_where_it_stopped(tmp_path):
    feitas = []

    def compute(part):
        if part.index == 7:
            raise KeyboardInterrupt
        feitas.append(part.index)
        return {"score": 1}

    todas = partitions([("brock",)], [1, 4, 7, 10])
    with pytest.raises(KeyboardInterrupt):
        run(todas, compute, tmp_path)
    assert feitas == [1, 4]

    assert [p.index for p in pending(todas, tmp_path)] == [7, 10]


def test_nothing_written_means_nothing_done(tmp_path):
    todas = partitions([("brock",), ("misty",)], [1])
    assert pending(todas, tmp_path) == todas


def test_a_partition_that_fails_does_not_poison_the_others(tmp_path):
    def compute(part):
        if part.index == 4:
            raise ValueError("dados em falta")
        return {"score": 1}

    todas = partitions([("brock",)], [1, 4, 7])
    falhadas = run(todas, compute, tmp_path, keep_going=True)
    assert [p.index for p in falhadas] == [4]
    assert [p.index for p in pending(todas, tmp_path)] == [4]
