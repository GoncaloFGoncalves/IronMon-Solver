import pytest

from mon.skew import profiles


def test_all_hybrid_profile_splits_bst_evenly():
    # Snorlax, BST 540. O perfil sem skew em nenhum dos tres pares poe
    # cada um dos seis stats em BST/6 = 90 (CONTEXT.md 3.2).
    hybrid = [p for p in profiles(540) if p.is_all_hybrid()]
    assert len(hybrid) == 1
    assert hybrid[0].as_tuple() == (90, 90, 90, 90, 90, 90)


def test_offensive_pair_concentrates_into_attack():
    # Snorlax, BST 540. No perfil physical o par (Atk, SpA) reparte-se em
    # BST/4 = 135 e BST/12 = 45; os outros pares ficam neutros em BST/6.
    physical = [p for p in profiles(540)
                if p.offensive == "physical"
                and p.defensive == "hybrid" and p.tempo == "hybrid"]
    assert len(physical) == 1
    assert physical[0].attack == 135
    assert physical[0].special_attack == 45
    assert physical[0].defense == 90


def test_defensive_and_tempo_pairs_skew_the_same_way():
    # Os tres pares tem o mesmo estatuto e a mesma formula (CONTEXT.md 3.2).
    # Snorlax, BST 540: def tank poe Def em 135 e SpD em 45;
    # fast poe Speed em 135 e HP em 45.
    by_key = {(p.offensive, p.defensive, p.tempo): p for p in profiles(540)}

    def_tank = by_key[("hybrid", "def_tank", "hybrid")]
    assert (def_tank.defense, def_tank.special_defense) == (135, 45)

    fast = by_key[("hybrid", "hybrid", "fast")]
    assert (fast.speed, fast.hp) == (135, 45)


def test_every_profile_conserves_the_bst():
    # Garantia central do modelo: 3 pares x 3 variantes = 27 perfis, e cada um
    # soma exatamente o BST (CONTEXT.md 3.2). BST 500 nao e divisivel por 12,
    # por isso apanha erros de arredondamento.
    all_profiles = profiles(500)
    assert len(all_profiles) == 27
    for p in all_profiles:
        assert sum(p.as_tuple()) == pytest.approx(500)
