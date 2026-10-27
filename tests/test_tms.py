from mon.tms import tms_available_at


def test_tms_accumulate_along_the_run():
    # A tabela de recolha e cumulativa: o que apanhaste antes continua contigo.
    assert len(tms_available_at("Brock")) == 3
    assert len(tms_available_at("Erika")) == 11
    assert len(tms_available_at("Elite 4")) == 25


def test_nothing_new_between_sabrina_and_blaine():
    # Nao ha TMs a apanhar entre os dois; o pool nao cresce.
    assert tms_available_at("Sabrina") == tms_available_at("Blaine")
