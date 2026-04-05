from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.elo import EloRating
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.services import system_settings_service as settings_svc
from app.services.user_presenter import user_to_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """Cadastro público: sempre como jogador (organizador é criado pelo admin)."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.player,
    )
    db.add(user)
    db.flush()
    init = settings_svc.get_initial_ranking_float(db)
    db.add(EloRating(user_id=user.id, rating=init, games_played=0))
    db.commit()
    db.refresh(user)
    return user_to_out(db, user)


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_to_out(db, user)
