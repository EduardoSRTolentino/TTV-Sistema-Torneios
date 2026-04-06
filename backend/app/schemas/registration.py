from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegistrationCreate(BaseModel):
    """Dupla: informe o e-mail do parceiro (deve estar cadastrado)."""
    partner_email: Optional[str] = Field(default=None, description="Obrigatório se torneio for duplas")


class RegistrationOut(BaseModel):
    id: int
    tournament_id: int
    user_id: int
    user_full_name: str
    user_rating: float
    partner_user_id: Optional[int]
    partner_full_name: Optional[str] = None
    partner_rating: Optional[float] = None
    created_at: datetime
    bracket_seed_rating: Optional[float] = None

    model_config = {"from_attributes": True}
