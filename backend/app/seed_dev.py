"""Popula dados de desenvolvimento (usuários/torneios/inscrições/ranking).

Execute na pasta `backend/`:
  python -m app.seed_dev

Idempotente: pode rodar várias vezes sem duplicar os registros principais.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.elo import EloRating
from app.models.registration import TournamentRegistration
from app.models.tournament import BracketFormat, GameFormat, Tournament, TournamentStatus
from app.models.user import User, UserRole
from app.security import hash_password


def _get_or_create_user(db: Session, *, email: str, full_name: str, role: UserRole, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Mantém o mesmo email, mas garante que nome e role estejam alinhados ao seed.
        user.full_name = full_name
        user.role = role
        return user
    user = User(email=email, full_name=full_name, role=role, hashed_password=hash_password(password))
    db.add(user)
    db.flush()
    return user


def _ensure_elo(db: Session, *, user_id: int, rating: float) -> None:
    row = db.query(EloRating).filter(EloRating.user_id == user_id).first()
    if row:
        row.rating = float(rating)
        return
    db.add(EloRating(user_id=user_id, rating=float(rating), games_played=0))


def _get_or_create_tournament(
    db: Session,
    *,
    title: str,
    organizer_id: int,
    game_format: GameFormat,
    status: TournamentStatus,
    max_participants: int = 32,
    days_from_now_deadline: int | None = 7,
    description: str | None = None,
    bracket_format: BracketFormat = BracketFormat.knockout,
) -> Tournament:
    t = db.query(Tournament).filter(Tournament.title == title).first()
    deadline = None
    if days_from_now_deadline is not None:
        deadline = datetime.now(timezone.utc) + timedelta(days=days_from_now_deadline)
    if t:
        t.organizer_id = organizer_id
        t.game_format = game_format
        t.bracket_format = bracket_format
        t.status = status
        t.max_participants = max_participants
        t.registration_deadline = deadline
        t.description = description
        return t
    t = Tournament(
        title=title,
        description=description,
        organizer_id=organizer_id,
        game_format=game_format,
        bracket_format=bracket_format,
        max_participants=max_participants,
        registration_deadline=deadline,
        status=status,
    )
    db.add(t)
    db.flush()
    return t


def _get_or_create_registration(
    db: Session, *, tournament_id: int, user_id: int, partner_user_id: int | None = None
) -> TournamentRegistration:
    reg = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.user_id == user_id,
        )
        .first()
    )
    if reg:
        reg.partner_user_id = partner_user_id
        return reg
    reg = TournamentRegistration(tournament_id=tournament_id, user_id=user_id, partner_user_id=partner_user_id)
    db.add(reg)
    db.flush()
    return reg


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Usuários
        organizer_pwd = "Organizador123!"
        player_pwd = "Jogador123!"

        org1 = _get_or_create_user(
            db, email="organizador1@ttv.com", full_name="Organizador 1", role=UserRole.organizer, password=organizer_pwd
        )
        org2 = _get_or_create_user(
            db, email="organizador2@ttv.com", full_name="Organizador 2", role=UserRole.organizer, password=organizer_pwd
        )

        players: list[User] = []
        for i, (name, rating) in enumerate(
            [
                ("Eduardo Jogador", 1650.0),
                ("Marina Jogadora", 1580.0),
                ("Rafa Jogador", 1520.0),
                ("Bia Jogadora", 1480.0),
                ("Caio Jogador", 1400.0),
                ("Lia Jogadora", 1720.0),
            ],
            start=1,
        ):
            u = _get_or_create_user(
                db,
                email=f"jogador{i}@ttv.com",
                full_name=name,
                role=UserRole.player,
                password=player_pwd,
            )
            players.append(u)
            _ensure_elo(db, user_id=u.id, rating=rating)

        # Torneios
        t1 = _get_or_create_tournament(
            db,
            title="TTV CUP (Individual) — Seed Dev",
            description="Torneio de teste (individual) com inscrições abertas.",
            organizer_id=org1.id,
            game_format=GameFormat.singles,
            bracket_format=BracketFormat.knockout,
            status=TournamentStatus.registration_open,
            max_participants=32,
            days_from_now_deadline=10,
        )
        t2 = _get_or_create_tournament(
            db,
            title="TTV DUO (Duplas) — Seed Dev",
            description="Torneio de teste (duplas) com inscrições abertas.",
            organizer_id=org2.id,
            game_format=GameFormat.doubles,
            bracket_format=BracketFormat.knockout,
            status=TournamentStatus.registration_open,
            max_participants=16,
            days_from_now_deadline=10,
        )
        t3 = _get_or_create_tournament(
            db,
            title="TTV CLOSED (Individual) — Seed Dev",
            description="Torneio de teste com inscrições fechadas.",
            organizer_id=org1.id,
            game_format=GameFormat.singles,
            bracket_format=BracketFormat.knockout,
            status=TournamentStatus.registration_closed,
            max_participants=32,
            days_from_now_deadline=None,
        )

        # Inscrições (individual)
        for p in players[:4]:
            _get_or_create_registration(db, tournament_id=t1.id, user_id=p.id)
        for p in players[2:6]:
            _get_or_create_registration(db, tournament_id=t3.id, user_id=p.id)

        # Inscrições (duplas) - uma inscrição por time (líder + parceiro)
        _get_or_create_registration(db, tournament_id=t2.id, user_id=players[0].id, partner_user_id=players[1].id)
        _get_or_create_registration(db, tournament_id=t2.id, user_id=players[2].id, partner_user_id=players[3].id)
        _get_or_create_registration(db, tournament_id=t2.id, user_id=players[4].id, partner_user_id=players[5].id)

        db.commit()

        print("Seed DEV concluído.")
        print("")
        print("Logins de teste:")
        print(f"- organizador1@ttv.com / {organizer_pwd}")
        print(f"- organizador2@ttv.com / {organizer_pwd}")
        print(f"- jogador1@ttv.com..jogador6@ttv.com / {player_pwd}")
        print("")
        print("Torneios criados:")
        print(f"- {t1.title}")
        print(f"- {t2.title}")
        print(f"- {t3.title}")
    finally:
        db.close()


if __name__ == "__main__":
    run()

