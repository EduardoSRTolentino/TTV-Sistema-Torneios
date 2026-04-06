"""Testes de seeding em serpente e classificação."""
from app.services.group_ranking import MatchLite, StandingAgg, rank_registrations
from app.services.group_service import snake_assign


def test_snake_eight_players_four_groups() -> None:
    ids = list(range(1, 9))
    g = snake_assign(ids, 4)
    assert len(g) == 4
    assert g[0] == [1, 8]
    assert g[1] == [2, 7]
    assert g[2] == [3, 6]
    assert g[3] == [4, 5]


def test_rank_two_players_by_points() -> None:
    a, b = 10, 20
    stats = {
        a: StandingAgg(points=3, wins=1, losses=0, sets_won=2, sets_lost=0, points_scored=22, points_conceded=10),
        b: StandingAgg(points=0, wins=0, losses=1, sets_won=0, sets_lost=2, points_scored=10, points_conceded=22),
    }
    matches = [MatchLite(reg1_id=a, reg2_id=b, winner_reg_id=a, reg1_sets_won=2, reg2_sets_won=0, reg1_points=22, reg2_points=10)]
    order = rank_registrations([a, b], stats, matches, None, {a: 1, b: 2}, 3, 0)
    assert order == [a, b]


def test_rank_head_to_head_two() -> None:
    a, b = 1, 2
    stats = {
        a: StandingAgg(points=3, wins=1, losses=1, sets_won=2, sets_lost=2, points_scored=44, points_conceded=44),
        b: StandingAgg(points=3, wins=1, losses=1, sets_won=2, sets_lost=2, points_scored=44, points_conceded=44),
    }
    matches = [
        MatchLite(reg1_id=a, reg2_id=b, winner_reg_id=a, reg1_sets_won=2, reg2_sets_won=0, reg1_points=22, reg2_points=10),
        MatchLite(reg1_id=a, reg2_id=b, winner_reg_id=b, reg1_sets_won=0, reg2_sets_won=2, reg1_points=10, reg2_points=22),
    ]
    order = rank_registrations([a, b], stats, matches, None, {a: 1, b: 2}, 3, 0)
    assert order[0] == a
