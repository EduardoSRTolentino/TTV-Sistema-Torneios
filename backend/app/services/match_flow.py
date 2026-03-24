"""Propaga vencedor para a próxima partida (MVP)."""
from sqlalchemy.orm import Session

from app.models.match import BracketMatch


def set_match_winner(db: Session, match: BracketMatch, winner_reg_id: int) -> None:
    if winner_reg_id not in (match.reg1_id, match.reg2_id):
        raise ValueError("O vencedor deve ser um dos jogadores desta partida.")
    match.winner_reg_id = winner_reg_id
    if match.next_match_id is None:
        return
    nxt = db.query(BracketMatch).filter(BracketMatch.id == match.next_match_id).first()
    if nxt is None:
        return
    if nxt.reg1_id is None:
        nxt.reg1_id = winner_reg_id
    elif nxt.reg2_id is None:
        nxt.reg2_id = winner_reg_id
    else:
        # Ambos preenchidos por erro de fluxo — sobrescreve slot vazio do mesmo feeder
        raise ValueError("Próxima partida já está completa.")
