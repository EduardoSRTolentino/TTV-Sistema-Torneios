from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_tournament_extra_columns() -> None:
    """Adiciona colunas novas em `tournaments` se o banco já existia antes delas (create_all não altera tabelas)."""
    insp = inspect(engine)
    if not insp.has_table("tournaments"):
        return
    existing = {c["name"].lower() for c in insp.get_columns("tournaments")}
    with engine.begin() as conn:
        if "registration_fee" not in existing:
            conn.execute(
                text("ALTER TABLE tournaments ADD COLUMN registration_fee DOUBLE NOT NULL DEFAULT 0")
            )
        if "prize" not in existing:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN prize TEXT NULL"))
        if "match_best_of_sets" not in existing:
            conn.execute(
                text("ALTER TABLE tournaments ADD COLUMN match_best_of_sets INT NOT NULL DEFAULT 3")
            )


def ensure_registration_extra_columns() -> None:
    insp = inspect(engine)
    if not insp.has_table("tournament_registrations"):
        return
    existing = {c["name"].lower() for c in insp.get_columns("tournament_registrations")}
    with engine.begin() as conn:
        if "bracket_seed_rating" not in existing:
            conn.execute(text("ALTER TABLE tournament_registrations ADD COLUMN bracket_seed_rating DOUBLE NULL"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
