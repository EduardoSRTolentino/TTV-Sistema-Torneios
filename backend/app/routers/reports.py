from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.services.audit_service import log_action

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreate(BaseModel):
    subject_type: str = Field(max_length=50)
    subject_id: Optional[int] = None
    body: str = Field(min_length=10, max_length=4000)


class ReportOut(BaseModel):
    id: int
    status: ReportStatus

    model_config = {"from_attributes": True}


@router.post("", response_model=ReportOut)
def create_report(
    body: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = Report(
        reporter_id=user.id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        body=body.body,
        status=ReportStatus.open,
    )
    db.add(r)
    log_action(db, actor_id=user.id, action="report.create", entity_type="report", entity_id=None, details={"subject": body.subject_type})
    db.commit()
    db.refresh(r)
    return r
