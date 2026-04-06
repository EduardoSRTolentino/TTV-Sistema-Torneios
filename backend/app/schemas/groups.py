from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class GroupMatchSetOut(BaseModel):
    set_number: int
    reg1_score: int
    reg2_score: int


class GroupStandingOut(BaseModel):
    registration_id: int
    display_name: str
    points: int
    wins: int
    losses: int
    sets_won: int
    sets_lost: int
    points_scored: int
    points_conceded: int
    rank_position: int
    initial_seed_rank: int


class GroupMatchOut(BaseModel):
    id: int
    group_id: int
    reg1_id: int
    reg2_id: int
    winner_reg_id: Optional[int]
    status: Literal["pending", "finished", "walkover"]
    match_order: int
    reg1_display: str = ""
    reg2_display: str = ""
    winner_display: Optional[str] = None
    sets: List[GroupMatchSetOut] = Field(default_factory=list)


class GroupDetailOut(BaseModel):
    id: int
    name: str
    sort_order: int
    standings: List[GroupStandingOut]
    matches: List[GroupMatchOut]


class GroupsPhaseOut(BaseModel):
    tournament_id: int
    groups: List[GroupDetailOut]


class MoveGroupMemberBody(BaseModel):
    registration_id: int = Field(ge=1)
    target_group_id: int = Field(ge=1)


class GroupWalkoverBody(BaseModel):
    winner_registration_id: int = Field(ge=1)
