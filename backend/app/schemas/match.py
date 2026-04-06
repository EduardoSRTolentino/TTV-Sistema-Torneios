from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class BracketMatchSetOut(BaseModel):
    set_number: int
    reg1_score: int
    reg2_score: int

    model_config = {"from_attributes": True}


class BracketMatchOut(BaseModel):
    id: int
    tournament_id: int
    round_number: int
    position_in_round: int
    match_order: int = 0
    bracket_round_key: Optional[str] = None
    bracket_position: Optional[int] = None
    reg1_id: Optional[int]
    reg2_id: Optional[int]
    winner_reg_id: Optional[int]
    next_match_id: Optional[int]
    status: Literal["pending", "in_progress", "finished"] = "pending"
    match_kind: Literal["knockout", "third_place"] = "knockout"
    round_label: str = ""
    reg1_display: str = ""
    reg2_display: str = ""
    winner_display: Optional[str] = None
    sets: List[BracketMatchSetOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SetWinnerBody(BaseModel):
    winner_registration_id: int


class MatchSetScoreIn(BaseModel):
    set_number: int = Field(ge=1)
    reg1_score: int = Field(ge=0)
    reg2_score: int = Field(ge=0)


class MatchResultBody(BaseModel):
    sets: List[MatchSetScoreIn]
