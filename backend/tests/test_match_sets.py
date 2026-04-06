"""Validação de placares de set (tênis de mesa)."""
import pytest

from app.models.match import BracketMatch, BracketMatchKind, BracketMatchStatus
from app.services.match_service import (
    SET_MIN_LEAD,
    infer_winner_registration_id_from_sets,
    is_valid_terminal_set,
    SetScoreRow,
)


def test_terminal_set_standard_wins() -> None:
    assert is_valid_terminal_set(11, 9, 11, SET_MIN_LEAD)
    assert is_valid_terminal_set(9, 11, 11, SET_MIN_LEAD)
    assert is_valid_terminal_set(11, 0, 11, SET_MIN_LEAD)


def test_terminal_set_invalid_one_point_margin_at_11() -> None:
    assert not is_valid_terminal_set(11, 10, 11, SET_MIN_LEAD)


def test_terminal_set_deuce_path() -> None:
    assert is_valid_terminal_set(12, 10, 11, SET_MIN_LEAD)
    assert is_valid_terminal_set(15, 13, 11, SET_MIN_LEAD)


def test_best_of_three_two_sets() -> None:
    m = BracketMatch(
        id=1,
        tournament_id=1,
        round_number=1,
        position_in_round=0,
        reg1_id=10,
        reg2_id=20,
        status=BracketMatchStatus.pending,
        match_kind=BracketMatchKind.knockout,
    )
    sets = [
        SetScoreRow(1, 11, 5),
        SetScoreRow(2, 11, 7),
    ]
    assert infer_winner_registration_id_from_sets(m, sets, best_of_sets=3, points_per_set=11) == 10


def test_rejects_extra_set_after_decided() -> None:
    m = BracketMatch(
        id=1,
        tournament_id=1,
        round_number=1,
        position_in_round=0,
        reg1_id=10,
        reg2_id=20,
        status=BracketMatchStatus.pending,
        match_kind=BracketMatchKind.knockout,
    )
    sets = [
        SetScoreRow(1, 11, 5),
        SetScoreRow(2, 11, 7),
        SetScoreRow(3, 11, 9),
    ]
    with pytest.raises(ValueError, match="Não envie sets"):
        infer_winner_registration_id_from_sets(m, sets, best_of_sets=3, points_per_set=11)


def test_incomplete_match() -> None:
    m = BracketMatch(
        id=1,
        tournament_id=1,
        round_number=1,
        position_in_round=0,
        reg1_id=10,
        reg2_id=20,
        status=BracketMatchStatus.pending,
        match_kind=BracketMatchKind.knockout,
    )
    sets = [SetScoreRow(1, 11, 9)]
    with pytest.raises(ValueError, match="incompleto"):
        infer_winner_registration_id_from_sets(m, sets, best_of_sets=3, points_per_set=11)
