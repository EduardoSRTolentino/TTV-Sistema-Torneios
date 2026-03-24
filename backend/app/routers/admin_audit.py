from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=List[AuditLogOut])
def list_logs(limit: int = 200, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(AuditLog).order_by(desc(AuditLog.id)).limit(min(limit, 1000)).all()
    return rows
