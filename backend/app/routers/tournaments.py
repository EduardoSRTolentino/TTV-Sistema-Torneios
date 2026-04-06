from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.elo import EloRating
from app.models.registration import TournamentRegistration
from app.models.tournament import GameFormat, Tournament, TournamentStatus
from app.models.user import User, UserRole
from app.models.match import BracketMatch
from app.schemas.match import BracketMatchOut, SetWinnerBody
from app.schemas.registration import RegistrationCreate, RegistrationOut
from app.schemas.tournament import TournamentCreate, TournamentOut, TournamentUpdate
from app.services.bracket import generate_knockout_bracket
from app.services.bracket_display import enrich_bracket_matches
from app.services.match_flow import set_match_winner
from app.services.tournament_lifecycle import (
    apply_auto_close_single,
    apply_auto_close_to_tournaments,
    apply_manual_close_registrations,
    start_tournament as start_tournament_flow,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

_org = Depends(require_roles(UserRole.organizer, UserRole.admin))


def _tournament_out(db: Session, t: Tournament) -> TournamentOut:
    cnt = db.query(func.count(TournamentRegistration.id)).filter(
        TournamentRegistration.tournament_id == t.id
    ).scalar()
    data = TournamentOut.model_validate(t)
    data = data.model_copy(update={"registrations_count": int(cnt or 0)})
    return data


@router.get("", response_model=List[TournamentOut])
def list_tournaments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.query(Tournament).order_by(Tournament.created_at.desc()).all()
    apply_auto_close_to_tournaments(db, rows)
    return [_tournament_out(db, t) for t in rows]


@router.get("/{tournament_id}", response_model=TournamentOut)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    apply_auto_close_single(db, t)
    return _tournament_out(db, t)


@router.post("", response_model=TournamentOut)
def create_tournament(
    body: TournamentCreate,
    db: Session = Depends(get_db),
    user: User = _org,
):
    t = Tournament(
        title=body.title,
        description=body.description,
        organizer_id=user.id,
        game_format=body.game_format,
        bracket_format=body.bracket_format,
        max_participants=body.max_participants,
        registration_fee=body.registration_fee,
        prize=body.prize,
        registration_deadline=body.registration_deadline,
        match_best_of_sets=body.match_best_of_sets,
        status=TournamentStatus.draft,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _tournament_out(db, t)


def _update_tournament_impl(
    tournament_id: int,
    body: TournamentUpdate,
    db: Session,
    user: User,
) -> TournamentOut:
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    if user.role != UserRole.admin and t.organizer_id != user.id:
        raise HTTPException(403, "Você não tem permissão para editar este torneio")

    data = body.model_dump(exclude_unset=True)
    if "max_participants" in data:
        cnt = (
            db.query(func.count(TournamentRegistration.id))
            .filter(TournamentRegistration.tournament_id == tournament_id)
            .scalar()
        )
        registered = int(cnt or 0)
        if data["max_participants"] < registered:
            raise HTTPException(
                400,
                "Número de vagas não pode ser menor que o total de inscritos",
            )

    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return _tournament_out(db, t)


@router.api_route("/{tournament_id}", methods=["PUT", "PATCH"], response_model=TournamentOut)
def update_tournament(
    tournament_id: int,
    body: TournamentUpdate,
    db: Session = Depends(get_db),
    user: User = _org,
):
    """Admin pode editar qualquer torneio; organizador apenas os que criou."""
    return _update_tournament_impl(tournament_id, body, db, user)


@router.post("/{tournament_id}/abrir-inscricoes", response_model=TournamentOut)
def open_registration(tournament_id: int, db: Session = Depends(get_db), user: User = _org):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    if user.role != UserRole.admin and t.organizer_id != user.id:
        raise HTTPException(403, "Apenas o organizador ou admin")
    t.status = TournamentStatus.registration_open
    db.commit()
    db.refresh(t)
    apply_auto_close_single(db, t)
    return _tournament_out(db, t)


def _require_tournament_manager(tournament_id: int, db: Session, user: User) -> Tournament:
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    if user.role != UserRole.admin and t.organizer_id != user.id:
        raise HTTPException(403, "Apenas o organizador ou admin")
    return t


@router.post("/{tournament_id}/fechar-inscricoes", response_model=TournamentOut)
def close_registration(tournament_id: int, db: Session = Depends(get_db), user: User = _org):
    t = _require_tournament_manager(tournament_id, db, user)
    apply_auto_close_single(db, t)
    try:
        apply_manual_close_registrations(t)
    except ValueError as e:
        raise HTTPException(400, str(e))
    db.commit()
    db.refresh(t)
    return _tournament_out(db, t)


@router.patch("/{tournament_id}/close-registrations", response_model=TournamentOut)
def patch_close_registrations(tournament_id: int, db: Session = Depends(get_db), user: User = _org):
    """Encerra inscrições manualmente (idempotente se já encerradas)."""
    return close_registration(tournament_id, db, user)


@router.patch("/{tournament_id}/start", response_model=TournamentOut)
def patch_start_tournament(tournament_id: int, db: Session = Depends(get_db), user: User = _org):
    """
    Inicia o torneio: fecha inscrições se ainda estiverem abertas, gera chaveamento (se necessário)
    e define status em andamento.
    """
    t = _require_tournament_manager(tournament_id, db, user)
    apply_auto_close_single(db, t)
    try:
        start_tournament_flow(db, t)
        db.commit()
        db.refresh(t)
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))
    return _tournament_out(db, t)


@router.post("/{tournament_id}/inscricao", response_model=RegistrationOut)
def register_player(
    tournament_id: int,
    body: RegistrationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    apply_auto_close_single(db, t)
    if t.status != TournamentStatus.registration_open:
        raise HTTPException(400, "Inscrições não estão abertas")
    now = datetime.now(timezone.utc)
    if t.registration_deadline and t.registration_deadline.tzinfo is None:
        deadline = t.registration_deadline.replace(tzinfo=timezone.utc)
    else:
        deadline = t.registration_deadline
    if deadline and now > deadline:
        raise HTTPException(400, "Prazo de inscrição encerrado")

    count = (
        db.query(func.count(TournamentRegistration.id))
        .filter(TournamentRegistration.tournament_id == tournament_id)
        .scalar()
    )
    if int(count or 0) >= t.max_participants:
        raise HTTPException(400, "Limite de vagas atingido")

    if db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.user_id == user.id,
    ).first():
        raise HTTPException(400, "Você já está inscrito neste torneio")

    partner_id = None
    if t.game_format == GameFormat.doubles:
        if not body.partner_email:
            raise HTTPException(400, "Informe o e-mail do parceiro (torneio em duplas)")
        partner = db.query(User).filter(User.email == body.partner_email).first()
        if not partner or partner.id == user.id:
            raise HTTPException(400, "Parceiro inválido")
        partner_id = partner.id
    elif body.partner_email:
        raise HTTPException(400, "Parceiro só é necessário em torneios de duplas")

    reg = TournamentRegistration(
        tournament_id=tournament_id,
        user_id=user.id,
        partner_user_id=partner_id,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


@router.get("/{tournament_id}/inscricoes", response_model=List[RegistrationOut])
def list_registrations(
    tournament_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    apply_auto_close_single(db, t)

    U1 = aliased(User)
    U2 = aliased(User)
    E1 = aliased(EloRating)
    E2 = aliased(EloRating)

    rows = (
        db.query(TournamentRegistration, U1, E1, U2, E2)
        .join(U1, U1.id == TournamentRegistration.user_id)
        .outerjoin(E1, E1.user_id == U1.id)
        .outerjoin(U2, U2.id == TournamentRegistration.partner_user_id)
        .outerjoin(E2, E2.user_id == U2.id)
        .filter(TournamentRegistration.tournament_id == tournament_id)
        .order_by(TournamentRegistration.id)
        .all()
    )

    out: List[RegistrationOut] = []
    for reg, user, elo, partner, partner_elo in rows:
        out.append(
            RegistrationOut(
                id=reg.id,
                tournament_id=reg.tournament_id,
                user_id=reg.user_id,
                user_full_name=user.full_name,
                user_rating=float(elo.rating) if elo else 1500.0,
                partner_user_id=reg.partner_user_id,
                partner_full_name=(partner.full_name if partner else None),
                partner_rating=(float(partner_elo.rating) if partner_elo else (1500.0 if partner else None)),
                created_at=reg.created_at,
                bracket_seed_rating=reg.bracket_seed_rating,
            )
        )
    return out


@router.post("/{tournament_id}/gerar-chaveamento", response_model=List[BracketMatchOut])
def generate_bracket(tournament_id: int, db: Session = Depends(get_db), user: User = _org):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    if user.role != UserRole.admin and t.organizer_id != user.id:
        raise HTTPException(403, "Apenas o organizador ou admin")
    apply_auto_close_single(db, t)
    if t.status != TournamentStatus.registration_closed:
        raise HTTPException(400, "Encerre as inscrições antes de gerar o chaveamento.")
    try:
        generate_knockout_bracket(db, t)
        db.commit()
        db.refresh(t)
        rows = (
            db.query(BracketMatch)
            .filter(BracketMatch.tournament_id == tournament_id)
            .order_by(BracketMatch.round_number, BracketMatch.position_in_round)
            .all()
        )
        return enrich_bracket_matches(db, t, rows)
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))


@router.get("/{tournament_id}/chaveamento", response_model=List[BracketMatchOut])
def get_bracket(
    tournament_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    apply_auto_close_single(db, t)
    rows = (
        db.query(BracketMatch)
        .filter(BracketMatch.tournament_id == tournament_id)
        .order_by(BracketMatch.round_number, BracketMatch.position_in_round)
        .all()
    )
    return enrich_bracket_matches(db, t, rows)


@router.post("/partidas/{match_id}/vencedor", response_model=BracketMatchOut)
def declare_winner(
    match_id: int,
    body: SetWinnerBody,
    db: Session = Depends(get_db),
    user: User = _org,
):
    m = db.query(BracketMatch).filter(BracketMatch.id == match_id).first()
    if not m:
        raise HTTPException(404, "Partida não encontrada")
    t = db.query(Tournament).filter(Tournament.id == m.tournament_id).first()
    if not t:
        raise HTTPException(404, "Torneio não encontrado")
    if user.role != UserRole.admin and t.organizer_id != user.id:
        raise HTTPException(403, "Apenas o organizador ou admin")
    try:
        set_match_winner(db, m, body.winner_registration_id)
        db.commit()
        db.refresh(m)
        return enrich_bracket_matches(db, t, [m])[0]
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))
