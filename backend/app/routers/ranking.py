from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.elo import EloRating
from app.models.user import User

router = APIRouter(prefix="/ranking", tags=["ranking"])


class RankingRow(BaseModel):
    user_id: int
    full_name: str
    rating: float
    games_played: int

    model_config = {"from_attributes": True}


@router.get("", response_model=List[RankingRow])
def global_ranking(limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(EloRating, User)
        .join(User, User.id == EloRating.user_id)
        .order_by(desc(EloRating.rating))
        .limit(min(limit, 500))
        .all()
    )
    out: List[RankingRow] = []
    for elo, user in rows:
        out.append(RankingRow(user_id=user.id, full_name=user.full_name, rating=elo.rating, games_played=elo.games_played))
    return out
