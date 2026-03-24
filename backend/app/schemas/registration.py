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
    partner_user_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
