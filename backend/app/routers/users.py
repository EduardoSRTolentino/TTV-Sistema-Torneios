from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.id != user_id and current.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return u


@router.post("", response_model=UserOut)
def create_user(
    body: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if current.id != user_id and current.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if body.full_name is not None:
        u.full_name = body.full_name
    if body.email is not None:
        if (
            db.query(User)
            .filter(User.email == body.email)
            .filter(User.id != user_id)
            .first()
        ):
            raise HTTPException(status_code=400, detail="E-mail já em uso")
        u.email = body.email
    db.commit()
    db.refresh(u)
    return u
