"""Classificação em grupo com critérios ordenados e mini-tabela em empates múltiplos."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set

DEFAULT_TIEBREAK_CRITERIA = [
    "points",
    "wins",
    "set_difference",
    "point_difference",
    "head_to_head",
    "initial_ranking",
]


@dataclass
class StandingAgg:
    points: int = 0
    wins: int = 0
    losses: int = 0
    sets_won: int = 0
    sets_lost: int = 0
    points_scored: int = 0
    points_conceded: int = 0


@dataclass
class MatchLite:
    reg1_id: int
    reg2_id: int
    winner_reg_id: Optional[int]
    reg1_sets_won: int = 0
    reg2_sets_won: int = 0
    reg1_points: int = 0
    reg2_points: int = 0


def build_stats_from_matches(
    subset: Set[int],
    matches: Sequence[MatchLite],
    points_win: int,
    points_loss: int,
) -> Dict[int, StandingAgg]:
    s: Dict[int, StandingAgg] = {rid: StandingAgg() for rid in subset}
    for m in matches:
        if m.winner_reg_id is None:
            continue
        if m.reg1_id not in subset or m.reg2_id not in subset:
            continue
        w = m.winner_reg_id
        l = m.reg2_id if w == m.reg1_id else m.reg1_id
        s[w].points += points_win
        s[l].points += points_loss
        s[w].wins += 1
        s[l].losses += 1
        if m.reg1_id == w:
            s[w].sets_won += m.reg1_sets_won
            s[w].sets_lost += m.reg2_sets_won
            s[l].sets_won += m.reg2_sets_won
            s[l].sets_lost += m.reg1_sets_won
            s[w].points_scored += m.reg1_points
            s[w].points_conceded += m.reg2_points
            s[l].points_scored += m.reg2_points
            s[l].points_conceded += m.reg1_points
        else:
            s[w].sets_won += m.reg2_sets_won
            s[w].sets_lost += m.reg1_sets_won
            s[l].sets_won += m.reg1_sets_won
            s[l].sets_lost += m.reg2_sets_won
            s[w].points_scored += m.reg2_points
            s[w].points_conceded += m.reg1_points
            s[l].points_scored += m.reg1_points
            s[l].points_conceded += m.reg2_points
    return s


def _head_to_head_winner(a: int, b: int, matches: Sequence[MatchLite]) -> Optional[int]:
    for m in matches:
        if m.winner_reg_id is None:
            continue
        if {m.reg1_id, m.reg2_id} != {a, b}:
            continue
        return m.winner_reg_id
    return None


def _compare_two(
    a: int,
    b: int,
    stats: Dict[int, StandingAgg],
    matches: Sequence[MatchLite],
    criteria: Sequence[str],
    initial_rank: Dict[int, int],
) -> int:
    """<0 se a classifica à frente de b."""
    for c in criteria:
        if c == "points":
            if stats[a].points != stats[b].points:
                return -(stats[a].points - stats[b].points)
        elif c == "wins":
            if stats[a].wins != stats[b].wins:
                return -(stats[a].wins - stats[b].wins)
        elif c == "set_difference":
            da = stats[a].sets_won - stats[a].sets_lost
            db = stats[b].sets_won - stats[b].sets_lost
            if da != db:
                return -(da - db)
        elif c == "point_difference":
            da = stats[a].points_scored - stats[a].points_conceded
            db = stats[b].points_scored - stats[b].points_conceded
            if da != db:
                return -(da - db)
        elif c == "head_to_head":
            hw = _head_to_head_winner(a, b, matches)
            if hw == a:
                return -1
            if hw == b:
                return 1
        elif c == "initial_ranking":
            ra, rb = initial_rank.get(a, 9999), initial_rank.get(b, 9999)
            if ra != rb:
                return ra - rb
    return 0


def _rank_block(
    block: List[int],
    full_stats: Dict[int, StandingAgg],
    matches: Sequence[MatchLite],
    criteria: Sequence[str],
    initial_rank: Dict[int, int],
    points_win: int,
    points_loss: int,
) -> List[int]:
    if len(block) <= 1:
        return block
    if len(block) >= 3:
        mini = build_stats_from_matches(set(block), matches, points_win, points_loss)

        def kt(rid: int) -> tuple:
            s = mini[rid]
            return (s.points, s.wins, s.sets_won - s.sets_lost, s.points_scored - s.points_conceded)

        if len({kt(r) for r in block}) == 1:
            return sorted(block, key=lambda r: initial_rank.get(r, 9999))
    if len(block) == 2:
        a, b = block[0], block[1]
        cmp = _compare_two(a, b, full_stats, matches, criteria, initial_rank)
        if cmp < 0:
            return [a, b]
        if cmp > 0:
            return [b, a]
        mini = build_stats_from_matches(set(block), matches, points_win, points_loss)
        cmp2 = _compare_two(a, b, mini, matches, criteria, initial_rank)
        if cmp2 < 0:
            return [a, b]
        if cmp2 > 0:
            return [b, a]
        return sorted([a, b], key=lambda r: initial_rank.get(r, 9999))

    sub = set(block)
    mini = build_stats_from_matches(sub, matches, points_win, points_loss)

    def kt(rid: int) -> tuple:
        s = mini[rid]
        return (s.points, s.wins, s.sets_won - s.sets_lost, s.points_scored - s.points_conceded)

    sub_sorted = sorted(block, key=lambda r: kt(r), reverse=True)
    out: List[int] = []
    i = 0
    while i < len(sub_sorted):
        j = i + 1
        while j < len(sub_sorted) and kt(sub_sorted[j]) == kt(sub_sorted[i]):
            j += 1
        inner = sub_sorted[i:j]
        if len(inner) == 1:
            out.extend(inner)
        else:
            out.extend(
                _rank_block(inner, full_stats, matches, criteria, initial_rank, points_win, points_loss)
            )
        i = j
    return out


def rank_registrations(
    registration_ids: Sequence[int],
    full_stats: Dict[int, StandingAgg],
    matches: Sequence[MatchLite],
    criteria: Optional[Sequence[str]],
    initial_rank: Dict[int, int],
    points_win: int,
    points_loss: int,
) -> List[int]:
    """Ordem final na classificação (melhor primeiro)."""
    crit = list(criteria) if criteria else DEFAULT_TIEBREAK_CRITERIA
    ids = [r for r in registration_ids if r in full_stats]
    if len(ids) <= 1:
        return ids

    def full_key(rid: int) -> tuple:
        s = full_stats[rid]
        return (s.points, s.wins, s.sets_won - s.sets_lost, s.points_scored - s.points_conceded)

    ids_sorted = sorted(ids, key=lambda r: full_key(r), reverse=True)
    out: List[int] = []
    i = 0
    while i < len(ids_sorted):
        j = i + 1
        while j < len(ids_sorted) and full_key(ids_sorted[j]) == full_key(ids_sorted[i]):
            j += 1
        block = ids_sorted[i:j]
        out.extend(_rank_block(block, full_stats, matches, crit, initial_rank, points_win, points_loss))
        i = j
    return out
