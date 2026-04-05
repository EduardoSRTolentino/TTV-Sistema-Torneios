from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.system_settings import SystemSettingsOut, SystemSettingsUpdate
from app.services import system_settings_service as settings_svc

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("", response_model=SystemSettingsOut)
def get_settings(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = settings_svc.get_settings_for_api(db)
    return SystemSettingsOut.model_validate(row)


@router.patch("", response_model=SystemSettingsOut)
def update_settings(
    body: SystemSettingsUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = settings_svc.upsert_initial_ranking(db, body.initial_ranking)
    db.commit()
    db.refresh(row)
    return row
