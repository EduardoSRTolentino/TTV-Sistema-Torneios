"""Testes da lógica de posicionamento competitivo e BYEs no mata-mata."""
import pytest

from app.services.bracket import (
    _next_power_of_2,
    competitive_bracket_seed_line,
    compute_first_round_slots,
    first_round_match_order_by_position,
    standard_bracket_seed_line,
)


def test_next_power_of_2() -> None:
    assert _next_power_of_2(1) == 1
    assert _next_power_of_2(2) == 2
    assert _next_power_of_2(5) == 8
    assert _next_power_of_2(8) == 8
    assert _next_power_of_2(9) == 16


def test_standard_line_eight() -> None:
    assert standard_bracket_seed_line(8) == [1, 8, 4, 5, 2, 7, 3, 6]


def test_competitive_line_eight() -> None:
    assert competitive_bracket_seed_line(8) == [1, 8, 4, 5, 3, 6, 2, 7]


def test_first_round_match_order_four_matches() -> None:
    assert first_round_match_order_by_position(4) == [1, 3, 2, 4]


def test_eight_players_competitive_pairing() -> None:
    ids = [101 + i for i in range(8)]
    slots = compute_first_round_slots(8, ids)
    assert slots[0:2] == [ids[0], ids[7]]
    assert slots[2:4] == [ids[3], ids[4]]
    assert slots[4:6] == [ids[2], ids[5]]
    assert slots[6:8] == [ids[1], ids[6]]


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
    # (1,8): seed8 missing → bye
    assert slots[0] == 1 and slots[1] is None
    # (4,5) partida real
    assert slots[2] == 4 and slots[3] == 5
    # (3,6)
    assert slots[4] == 3 and slots[5] is None
    # (2,7)
    assert slots[6] == 2 and slots[7] is None


def test_compute_first_round_wrong_length() -> None:
    with pytest.raises(ValueError):
        compute_first_round_slots(3, [1, 2])
