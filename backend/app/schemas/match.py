from typing import Optional

from pydantic import BaseModel


class BracketMatchOut(BaseModel):
    id: int
    tournament_id: int
    round_number: int
    position_in_round: int
    reg1_id: Optional[int]
    reg2_id: Optional[int]
    winner_reg_id: Optional[int]
    next_match_id: Optional[int]

    model_config = {"from_attributes": True}


class SetWinnerBody(BaseModel):
    winner_registration_id: int
