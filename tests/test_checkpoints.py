from mon.checkpoints import CHECKPOINTS, kaizo_levels
from mon.tms import TM_PICKUPS


def test_kaizo_levels_are_the_vanilla_ones_boosted():
    # O Kaizo aplica +50% aos niveis dos treinadores. O Brock vanilla e 12-14,
    # logo 18-21 no Kaizo (observado em jogo: 20, erro de -1).
    assert kaizo_levels(12, 14) == (18, 21)
    assert kaizo_levels(51, 63) == (76, 94)


def test_the_pool_shrinks_to_final_evolutions_from_erika_on():
    # Com forced evolution a ~30, o pool adversario passa a ser so de
    # evolucoes finais a partir do momento em que o nivel minimo passa os 30.
    # Lt. Surge ainda esta em 27-36; o Erika salta para 36-43.
    encolhe = {c.name: c.final_evolutions_only for c in CHECKPOINTS}
    assert encolhe["Lt. Surge"] is False
    assert encolhe["Erika"] is True
    assert all(encolhe[n] for n in ("Koga", "Blaine", "Giovanni", "Elite 4"))


def test_the_tm_table_uses_the_same_checkpoints():
    # Guarda de acoplamento: o tms.py indexa por nome de checkpoint. Se as
    # duas listas divergirem, tms_available_at rebenta com KeyError.
    assert [c.name for c in CHECKPOINTS] == [name for name, _ in TM_PICKUPS]
