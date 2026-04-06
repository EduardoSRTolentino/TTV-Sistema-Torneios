"""Pontos de premiação de torneios acumulados em `EloRating.ranking_points`."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.elo import EloRating
from app.models.match import BracketMatch, BracketMatchKind
from app.models.registration import TournamentRegistration
from app.models.tournament import GameFormat, Tournament


def _premio_for_position(premio: dict, position: int) -> float:
    key = str(position)
    v = premio.get(key)
    if v is None:
        v = premio.get(position)
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _loser_reg_id(m: BracketMatch) -> Optional[int]:
    if m.winner_reg_id is None or m.reg1_id is None or m.reg2_id is None:
        return None
    if m.winner_reg_id == m.reg1_id:
        return m.reg2_id
    return m.reg1_id


def build_tournament_placements(tournament: Tournament, matches: List[BracketMatch]) -> List[Tuple[int, List[int]]]:
    """
    Lista (posição, [registration_ids]) para distribuição de premiação.
    Posição 3 pode ter dois IDs empatados (sem disputa de 3º).
    """
    ko = [m for m in matches if m.match_kind == BracketMatchKind.knockout]
    if not ko:
        return []
    max_r = max(m.round_number for m in ko)
    finals = [m for m in ko if m.round_number == max_r and m.position_in_round == 0]
    if not finals:
        finals = [m for m in ko if m.round_number == max_r]
    final = finals[0] if len(finals) == 1 else min(finals, key=lambda x: x.position_in_round)
    if not final.winner_reg_id:
        return []
    champ = final.winner_reg_id
    runner = _loser_reg_id(final)
    out: List[Tuple[int, List[int]]] = [(1, [champ])]
    if runner is not None:
        out.append((2, [runner]))

    bronze = next((m for m in matches if m.match_kind == BracketMatchKind.third_place), None)
    if tournament.dispute_third_place and bronze and bronze.winner_reg_id:
        third = bronze.winner_reg_id
        fourth = _loser_reg_id(bronze)
        out.append((3, [third]))
        if fourth is not None:
            out.append((4, [fourth]))
        return out

    semis = [m for m in ko if m.round_number == max_r - 1]
    if len(semis) == 2:
        l1, l2 = _loser_reg_id(semis[0]), _loser_reg_id(semis[1])
        tied = [x for x in (l1, l2) if x is not None]
        if len(tied) == 2:
            out.append((3, tied))
    return out


def add_ranking_points_for_users(db: Session, user_ids: List[int], delta: float) -> None:
    if delta == 0:
        return
    for uid in user_ids:
        row = db.query(EloRating).filter(EloRating.user_id == uid).first()
        if row is None:
            row = EloRating(user_id=uid, rating=1500.0, ranking_points=0.0, games_played=0)
            db.add(row)
            db.flush()
        row.ranking_points = float(row.ranking_points or 0) + delta


def add_points_for_registration(db: Session, tournament: Tournament, registration_id: int, points: float) -> None:
    if points == 0:
        return
    reg = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.id == registration_id,
            TournamentRegistration.tournament_id == tournament.id,
        )
        .first()
    )
    if reg is None:
        return
    uids = [reg.user_id]
    if tournament.game_format == GameFormat.doubles and reg.partner_user_id:
        uids.append(reg.partner_user_id)
    add_ranking_points_for_users(db, uids, points)


def apply_tournament_ranking_prizes(db: Session, tournament: Tournament) -> None:
    premio: Optional[Dict[str, Any]] = tournament.ranking_premiacao
    if not premio or not isinstance(premio, dict):
        return
    matches = (
        db.query(BracketMatch).filter(BracketMatch.tournament_id == tournament.id).all()
    )
    placements = build_tournament_placements(tournament, matches)
    for position, reg_ids in placements:
        pts = _premio_for_position(premio, position)
        if pts == 0:
            continue
        for rid in reg_ids:
            add_points_for_registration(db, tournament, rid, pts)
