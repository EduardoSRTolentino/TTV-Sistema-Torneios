from sqlalchemy.orm import Session

from app.models.elo import EloRating
from app.models.user import User
from app.schemas.user import UserOut


def user_to_out(db: Session, user: User) -> UserOut:
    elo = db.query(EloRating).filter(EloRating.user_id == user.id).first()
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at,
        rating=float(elo.rating) if elo else None,
    )
