"""Propaga vencedores para a próxima partida (esquerda → reg1, direita → reg2) e BYEs só na 1ª rodada."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.match import BracketMatch, BracketMatchStatus
from app.models.tournament import Tournament, TournamentStatus


def _match_is_bye_pending(m: BracketMatch) -> bool:
    if m.winner_reg_id is not None:
        return False
    r1, r2 = m.reg1_id, m.reg2_id
    return (r1 is not None and r2 is None) or (r2 is not None and r1 is None)


def _apply_bye_winner_if_pending(db: Session, m: BracketMatch) -> bool:
    if not _match_is_bye_pending(m):
        return False
    if m.reg1_id is not None and m.reg2_id is None:
        m.winner_reg_id = m.reg1_id
    else:
        m.winner_reg_id = m.reg2_id
    return True


def advance_winner_into_next_match(db: Session, match: BracketMatch) -> Optional[BracketMatch]:
    """
    Coloca o vencedor da partida no slot correto da próxima:
    posição par na rodada → alimenta reg1; ímpar → reg2.
    """
    w = match.winner_reg_id
    if w is None or match.next_match_id is None:
        return None
    nxt = db.query(BracketMatch).filter(BracketMatch.id == match.next_match_id).first()
    if nxt is None:
        return None
    if w in (nxt.reg1_id, nxt.reg2_id):
        return nxt
    feeds_reg1 = match.position_in_round % 2 == 0
    if feeds_reg1:
        if nxt.reg1_id is None:
            nxt.reg1_id = w
        else:
            raise ValueError("Slot reg1 da próxima partida já está ocupado.")
    else:
        if nxt.reg2_id is None:
            nxt.reg2_id = w
        else:
            raise ValueError("Slot reg2 da próxima partida já está ocupado.")
    return nxt


def try_advance_match_winner_to_parent(db: Session, m: BracketMatch) -> bool:
    """Retorna True se propagou o vencedor de m para o pai."""
    before = (m.winner_reg_id, m.next_match_id)
    if before[0] is None or before[1] is None:
        return False
    nxt = db.query(BracketMatch).filter(BracketMatch.id == m.next_match_id).first()
    if nxt is None:
        return False
    w = m.winner_reg_id
    if w in (nxt.reg1_id, nxt.reg2_id):
        return False
    feeds_reg1 = m.position_in_round % 2 == 0
    if feeds_reg1 and nxt.reg1_id is None:
        nxt.reg1_id = w
        return True
    if not feeds_reg1 and nxt.reg2_id is None:
        nxt.reg2_id = w
        return True
    return False


def settle_tournament_propagations(db: Session, tournament_id: int) -> None:
    """
    Até estabilizar: aplica BYEs só na rodada 1 e propaga vencedores para os pais
    quando o slot correspondente estiver livre.
    """
    for _ in range(128):
        changed = False
        matches = (
            db.query(BracketMatch)
            .filter(BracketMatch.tournament_id == tournament_id)
            .order_by(BracketMatch.round_number, BracketMatch.match_order, BracketMatch.position_in_round)
            .all()
        )
        for m in matches:
            if m.winner_reg_id is None and m.round_number == 1 and _apply_bye_winner_if_pending(db, m):
                changed = True
                db.flush()
            elif m.winner_reg_id is not None and try_advance_match_winner_to_parent(db, m):
                changed = True
                db.flush()
        if not changed:
            break


def set_match_winner(db: Session, match: BracketMatch, winner_reg_id: int) -> None:
    t = db.query(Tournament).filter(Tournament.id == match.tournament_id).first()
    if t is not None and t.status == TournamentStatus.completed:
        raise ValueError("Torneio finalizado.")
    if match.status == BracketMatchStatus.finished:
        raise ValueError("Partida já finalizada.")
    if winner_reg_id not in (match.reg1_id, match.reg2_id):
        raise ValueError("O vencedor deve ser um dos jogadores desta partida.")
    match.winner_reg_id = winner_reg_id
    match.status = BracketMatchStatus.finished
    db.flush()
    advance_winner_into_next_match(db, match)
    db.flush()
    settle_tournament_propagations(db, match.tournament_id)
    from app.services.tournament_service import after_match_resolved

    after_match_resolved(db, match.tournament_id)


def propagate_initial_bye_winners(db: Session, first_round_matches: list[BracketMatch]) -> None:
    if not first_round_matches:
        return
    settle_tournament_propagations(db, first_round_matches[0].tournament_id)
