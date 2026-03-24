"""Pagamentos Pix + comprovante (upload local seguro em disco)."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.payment import Payment, PaymentStatus
from app.models.tournament import Tournament
from app.models.user import User, UserRole
from app.services.audit_service import log_action

router = APIRouter(prefix="/payments", tags=["payments"])

UPLOAD_ROOT = Path(os.getenv("TTV_UPLOAD_DIR", "uploads"))
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".pdf"}


class PaymentOut(BaseModel):
    id: int
    status: PaymentStatus
    amount_cents: int

    model_config = {"from_attributes": True}


def _save_proof(file: UploadFile) -> str:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "file").suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, "Formato não permitido (use JPG, PNG ou PDF)")
    name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / name
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande (máx. 5MB)")
    dest.write_bytes(data)
    return str(dest)


@router.post("/torneios/{tournament_id}", response_model=PaymentOut)
def create_payment_with_proof(
    tournament_id: int,
    amount_cents: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    path = _save_proof(file)
    pay = Payment(
        tournament_id=tournament_id,
        user_id=user.id,
        amount_cents=amount_cents,
        status=PaymentStatus.pending,
        proof_file_path=path,
    )
    db.add(pay)
    log_action(db, actor_id=user.id, action="payment.create", entity_type="payment", entity_id=None, details={"tournament_id": tournament_id})
    db.commit()
    db.refresh(pay)
    return pay


@router.post("/{payment_id}/confirmar", response_model=PaymentOut)
def confirm_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in (UserRole.admin, UserRole.organizer):
        raise HTTPException(403, "Sem permissão")
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(404, "Pagamento não encontrado")
    t = db.query(Tournament).filter(Tournament.id == p.tournament_id).first()
    if user.role != UserRole.admin and t and t.organizer_id != user.id:
        raise HTTPException(403, "Apenas o organizador deste torneio")
    p.status = PaymentStatus.confirmed
    p.confirmed_by_user_id = user.id
    log_action(db, actor_id=user.id, action="payment.confirm", entity_type="payment", entity_id=p.id)
    db.commit()
    db.refresh(p)
    return p
