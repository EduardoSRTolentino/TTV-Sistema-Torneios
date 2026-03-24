"""ELO simplificado (Fase 2): atualização após resultado conhecido."""
from sqlalchemy.orm import Session

from app.models.elo import EloRating


def get_or_create_rating(db: Session, user_id: int) -> EloRating:
    row = db.query(EloRating).filter(EloRating.user_id == user_id).first()
    if row:
        return row
    row = EloRating(user_id=user_id)
    db.add(row)
    db.flush()
    return row


def update_elo_after_match(db: Session, winner_user_id: int, loser_user_id: int, k: float = 32.0) -> tuple[float, float]:
    """Retorna (rating_vencedor_novo, rating_perdedor_novo)."""
    w = get_or_create_rating(db, winner_user_id)
    l = get_or_create_rating(db, loser_user_id)
    rw, rl = w.rating, l.rating
    ew = 1 / (1 + 10 ** ((rl - rw) / 400))
    el = 1 / (1 + 10 ** ((rw - rl) / 400))
    w.rating = rw + k * (1 - ew)
    l.rating = rl + k * (0 - el)
    w.games_played += 1
    l.games_played += 1
    return w.rating, l.rating
