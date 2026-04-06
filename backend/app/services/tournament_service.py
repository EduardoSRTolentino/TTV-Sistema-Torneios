"""Criação da disputa de 3º lugar e encerramento do torneio com premiação."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.match import BracketMatch, BracketMatchKind, BracketMatchStatus
from app.models.tournament import Tournament, TournamentStatus
from app.services.ranking_service import apply_tournament_ranking_prizes


def _loser_reg_id(m: BracketMatch) -> int | None:
    if m.winner_reg_id is None or m.reg1_id is None or m.reg2_id is None:
        return None
    if m.winner_reg_id == m.reg1_id:
        return m.reg2_id
    return m.reg1_id


def ensure_third_place_match(db: Session, t: Tournament) -> None:
    if not t.dispute_third_place or t.status != TournamentStatus.in_progress:
        return
    matches = db.query(BracketMatch).filter(BracketMatch.tournament_id == t.id).all()
    if any(m.match_kind == BracketMatchKind.third_place for m in matches):
        return
    ko = [m for m in matches if m.match_kind == BracketMatchKind.knockout]
    if not ko:
        return
    max_r = max(m.round_number for m in ko)
    if max_r < 2:
        return
    semis = [m for m in ko if m.round_number == max_r - 1]
    if len(semis) != 2:
        return
    if any(m.winner_reg_id is None for m in semis):
        return
    l1, l2 = _loser_reg_id(semis[0]), _loser_reg_id(semis[1])
    if l1 is None or l2 is None or l1 == l2:
        return
    bronze = BracketMatch(
        tournament_id=t.id,
        round_number=max_r,
        position_in_round=1,
        reg1_id=l1,
        reg2_id=l2,
        winner_reg_id=None,
        next_match_id=None,
        status=BracketMatchStatus.pending,
        match_kind=BracketMatchKind.third_place,
        match_order=2,
        bracket_round_key="third_place",
        bracket_position=None,
    )
    db.add(bronze)
    db.flush()


def try_complete_tournament(db: Session, t: Tournament) -> None:
    if t.status != TournamentStatus.in_progress:
        return
    matches = db.query(BracketMatch).filter(BracketMatch.tournament_id == t.id).all()
    ko = [m for m in matches if m.match_kind == BracketMatchKind.knockout]
    if not ko:
        return
    max_r = max(m.round_number for m in ko)
    finals = [m for m in ko if m.round_number == max_r and m.position_in_round == 0]
    if not finals:
        finals = [m for m in ko if m.round_number == max_r]
    final = finals[0] if len(finals) == 1 else min(finals, key=lambda x: x.position_in_round)
    if final.winner_reg_id is None:
        return
    if t.dispute_third_place and max_r >= 2:
        bronze = next((m for m in matches if m.match_kind == BracketMatchKind.third_place), None)
        if bronze is None or bronze.winner_reg_id is None:
            return
    t.status = TournamentStatus.completed
    db.flush()
    apply_tournament_ranking_prizes(db, t)
    db.flush()


def after_match_resolved(db: Session, tournament_id: int) -> None:
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if t is None:
        return
    ensure_third_place_match(db, t)
    try_complete_tournament(db, t)
