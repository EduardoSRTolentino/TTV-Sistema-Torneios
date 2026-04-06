"""Testes da lógica de posicionamento 1 vs último e BYEs no mata-mata."""
import pytest

from app.services.bracket import _next_power_of_2, compute_first_round_slots


def test_next_power_of_2() -> None:
    assert _next_power_of_2(1) == 1
    assert _next_power_of_2(2) == 2
    assert _next_power_of_2(5) == 8
    assert _next_power_of_2(8) == 8
    assert _next_power_of_2(9) == 16


def test_eight_players_classic_pairing() -> None:
    ids = [101 + i for i in range(8)]
    slots = compute_first_round_slots(8, ids)
    assert slots[0:2] == [ids[0], ids[7]]
    assert slots[2:4] == [ids[1], ids[6]]
    assert slots[4:6] == [ids[2], ids[5]]
    assert slots[6:8] == [ids[3], ids[4]]


def test_ten_players_all_seeded_once_with_byes() -> None:
    n = 10
    ids = list(range(1, 11))
    slots = compute_first_round_slots(n, ids)
    assert len(slots) == 16
    present = [x for x in slots if x is not None]
    assert len(present) == 10
    assert sorted(present) == ids


def test_five_players_bye_top_seeds() -> None:
    ids = [1, 2, 3, 4, 5]
    slots = compute_first_round_slots(5, ids)
    S = 8
    assert len(slots) == S
    # (1,8): seed8 missing → bye for 1
    assert slots[0] == 1 and slots[1] is None
    # (2,7)
    assert slots[2] == 2 and slots[3] is None
    # (3,6)
    assert slots[4] == 3 and slots[5] is None
    # (4,5) real match
    assert slots[6] == 4 and slots[7] == 5


def test_compute_first_round_wrong_length() -> None:
    with pytest.raises(ValueError):
        compute_first_round_slots(3, [1, 2])
