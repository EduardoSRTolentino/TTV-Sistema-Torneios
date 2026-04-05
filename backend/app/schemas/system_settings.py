from pydantic import BaseModel, Field


class SystemSettingsOut(BaseModel):
    id: int
    initial_ranking: int

    model_config = {"from_attributes": True}


class SystemSettingsUpdate(BaseModel):
    initial_ranking: int = Field(ge=0)
