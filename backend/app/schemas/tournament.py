from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.tournament import GameFormat, BracketFormat, TournamentStatus


class TournamentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    game_format: GameFormat = GameFormat.singles
    bracket_format: BracketFormat = BracketFormat.knockout
    max_participants: int = Field(ge=2, le=512)
    registration_fee: float = Field(default=0.0, ge=0)
    prize: Optional[str] = None
    registration_deadline: Optional[datetime] = None
    match_best_of_sets: int = Field(default=3, ge=1, le=9)

    @field_validator("match_best_of_sets")
    @classmethod
    def odd_best_of(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError("Número de sets deve ser ímpar (ex.: 1, 3, 5).")
        return v


class TournamentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    max_participants: Optional[int] = Field(default=None, ge=2, le=512)
    registration_fee: Optional[float] = Field(default=None, ge=0)
    prize: Optional[str] = None
    registration_deadline: Optional[datetime] = None
    status: Optional[TournamentStatus] = None
    match_best_of_sets: Optional[int] = Field(default=None, ge=1, le=9)

    @field_validator("match_best_of_sets")
    @classmethod
    def odd_best_of_upd(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v % 2 == 0:
            raise ValueError("Número de sets deve ser ímpar (ex.: 1, 3, 5).")
        return v

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("O nome do torneio não pode ser vazio")
        return s

    @field_validator("prize")
    @classmethod
    def empty_prize_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class TournamentOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    organizer_id: int
    game_format: GameFormat
    bracket_format: BracketFormat
    max_participants: int
    registration_fee: float
    prize: Optional[str]
    registration_deadline: Optional[datetime]
    match_best_of_sets: int = 3
    status: TournamentStatus
    created_at: datetime
    registrations_count: int = 0

    model_config = {"from_attributes": True}
