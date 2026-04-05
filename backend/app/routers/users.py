from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.elo import EloRating
from app.models.user import User, UserRole
from app.schemas.user import AdminUserUpdate, UserCreate, UserOut, UserRankingPatch, UserUpdate
from app.security import hash_password
from app.services import system_settings_service as settings_svc
from app.services.user_presenter import user_to_out

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return [user_to_out(db, u) for u in users]


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
    return user_to_out(db, u)


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
    db.flush()
    init = settings_svc.get_initial_ranking_float(db)
    db.add(EloRating(user_id=user.id, rating=init, games_played=0))
    db.commit()
    db.refresh(user)
    return user_to_out(db, user)


@router.patch("/{user_id}/ranking", response_model=UserOut)
def patch_user_ranking(
    user_id: int,
    body: UserRankingPatch,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    elo = db.query(EloRating).filter(EloRating.user_id == user_id).first()
    if elo is None:
        db.add(EloRating(user_id=user_id, rating=body.ranking, games_played=0))
    else:
        elo.rating = body.ranking
    db.commit()
    db.refresh(u)
    return user_to_out(db, u)


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
    return user_to_out(db, u)


@router.patch("/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: int,
    body: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if admin.id == user_id:
        raise HTTPException(
            status_code=403,
            detail="Administradores não podem alterar o próprio cargo.",
        )
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    u.role = body.role
    db.commit()
    db.refresh(u)
    return user_to_out(db, u)
