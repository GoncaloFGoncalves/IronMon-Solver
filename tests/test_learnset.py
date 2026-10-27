from mon.learnset import learn_schedule, moves_known_at


def test_level_one_is_padded_up_to_four_moves():
    # Bulbasaur aprende, no FRLG vanilla, 1 move ao nivel 1 e depois
    # 4, 7, 10, 15, 15, 20, 25, 32, 39, 46. O Kaizo garante 4 moves a saida
    # do lab, por isso o nivel 1 e preenchido ate 4.
    vanilla = [1, 4, 7, 10, 15, 15, 20, 25, 32, 39, 46]
    assert learn_schedule(vanilla) == (
        1, 1, 1, 1, 4, 7, 10, 15, 15, 20, 25, 32, 39, 46)


def test_padding_never_truncates():
    # O Victreebel aprende 7 moves ao nivel 1 no vanilla e nada acima disso.
    # Preencher "ate 4" nao pode cortar os 7 que ja la estavam -- foi este o
    # caso que invalidou a primeira versao da regra.
    assert learn_schedule([1] * 7) == (1,) * 7


def test_moves_known_at_a_level():
    # O que o solver precisa: quantos moves ja foram aprendidos a um nivel.
    schedule = learn_schedule([1, 4, 7, 10, 15, 15, 20, 25, 32, 39, 46])
    assert moves_known_at(schedule, level=1) == 4
    assert moves_known_at(schedule, level=7) == 6
    assert moves_known_at(schedule, level=15) == 9
    assert moves_known_at(schedule, level=100) == 14
