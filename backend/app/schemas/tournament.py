from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.tournament import GameFormat, BracketFormat, TournamentStatus


class TournamentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    game_format: GameFormat = GameFormat.singles
    bracket_format: BracketFormat = BracketFormat.knockout
    max_participants: int = Field(ge=2, le=512)
    registration_deadline: Optional[datetime] = None


class TournamentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_participants: Optional[int] = Field(default=None, ge=2, le=512)
    registration_deadline: Optional[datetime] = None
    status: Optional[TournamentStatus] = None


class TournamentOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    organizer_id: int
    game_format: GameFormat
    bracket_format: BracketFormat
    max_participants: int
    registration_deadline: Optional[datetime]
    status: TournamentStatus
    created_at: datetime
    registrations_count: int = 0

    model_config = {"from_attributes": True}
