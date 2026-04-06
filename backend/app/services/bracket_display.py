"""Rótulos de fase e nomes para exibição do chaveamento."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.match import BracketMatch
from app.models.registration import TournamentRegistration
from app.models.tournament import GameFormat, Tournament
from app.models.user import User
from app.schemas.match import BracketMatchOut


def phase_label(round_number: int, total_rounds: int) -> str:
    """round_number 1 = primeira fase (mais jogos); total_rounds = final."""
    if total_rounds < 1:
        return f"Rodada {round_number}"
    d = total_rounds - round_number
    if d == 0:
        return "Final"
    if d == 1:
        return "Semifinal"
    if d == 2:
        return "Quartas de final"
    if d == 3:
        return "Oitavas de final"
    return f"Rodada {round_number}"


def _registration_label(db: Session, reg: Optional[TournamentRegistration], game_format: GameFormat) -> str:
    if reg is None:
        return "Bye"
    u1 = db.query(User).filter(User.id == reg.user_id).first()
    n1 = u1.full_name if u1 else f"#{reg.user_id}"
    if game_format == GameFormat.doubles and reg.partner_user_id:
        u2 = db.query(User).filter(User.id == reg.partner_user_id).first()
        n2 = u2.full_name if u2 else f"#{reg.partner_user_id}"
        return f"{n1} + {n2}"
    return n1


def _load_registration_map(db: Session, tournament_id: int) -> Dict[int, TournamentRegistration]:
    rows = (
        db.query(TournamentRegistration).filter(TournamentRegistration.tournament_id == tournament_id).all()
    )
    return {r.id: r for r in rows}


def _slot_label(
    db: Session,
    reg: Optional[TournamentRegistration],
    reg_id: Optional[int],
    game_format: GameFormat,
) -> str:
    if reg_id is None:
        return "Bye"
    if reg is None:
        return f"Inscrição #{reg_id}"
    return _registration_label(db, reg, game_format)


def enrich_bracket_matches(db: Session, tournament: Tournament, matches: List[BracketMatch]) -> List[BracketMatchOut]:
    if not matches:
        return []
    total_rounds = max(m.round_number for m in matches)
    reg_map = _load_registration_map(db, tournament.id)
    out: list[BracketMatchOut] = []
    for m in matches:
        r1 = reg_map.get(m.reg1_id) if m.reg1_id else None
        r2 = reg_map.get(m.reg2_id) if m.reg2_id else None
        rw = reg_map.get(m.winner_reg_id) if m.winner_reg_id else None
        wdisp = (
            _slot_label(db, rw, m.winner_reg_id, tournament.game_format) if m.winner_reg_id else None
        )
        out.append(
            BracketMatchOut(
                id=m.id,
                tournament_id=m.tournament_id,
                round_number=m.round_number,
                position_in_round=m.position_in_round,
                reg1_id=m.reg1_id,
                reg2_id=m.reg2_id,
                winner_reg_id=m.winner_reg_id,
                next_match_id=m.next_match_id,
                round_label=phase_label(m.round_number, total_rounds),
                reg1_display=_slot_label(db, r1, m.reg1_id, tournament.game_format),
                reg2_display=_slot_label(db, r2, m.reg2_id, tournament.game_format),
                winner_display=wdisp,
            )
        )
    return out
