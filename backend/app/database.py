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


def ensure_tournament_match_scoring_columns() -> None:
    insp = inspect(engine)
    if not insp.has_table("tournaments"):
        return
    existing = {c["name"].lower() for c in insp.get_columns("tournaments")}
    with engine.begin() as conn:
        if "match_points_per_set" not in existing:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN match_points_per_set INT NOT NULL DEFAULT 11"))
        if "dispute_third_place" not in existing:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN dispute_third_place TINYINT(1) NOT NULL DEFAULT 0"))
        if "ranking_premiacao" not in existing:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN ranking_premiacao JSON NULL"))


def ensure_elo_ranking_points_column() -> None:
    insp = inspect(engine)
    if not insp.has_table("elo_ratings"):
        return
    existing = {c["name"].lower() for c in insp.get_columns("elo_ratings")}
    with engine.begin() as conn:
        if "ranking_points" not in existing:
            conn.execute(text("ALTER TABLE elo_ratings ADD COLUMN ranking_points DOUBLE NOT NULL DEFAULT 0"))


def ensure_bracket_match_extra_columns() -> None:
    insp = inspect(engine)
    if not insp.has_table("bracket_matches"):
        return
    existing = {c["name"].lower() for c in insp.get_columns("bracket_matches")}
    with engine.begin() as conn:
        if "status" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE bracket_matches ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'pending'"
                )
            )
        if "match_kind" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE bracket_matches ADD COLUMN match_kind VARCHAR(32) NOT NULL DEFAULT 'knockout'"
                )
            )
        conn.execute(
            text("UPDATE bracket_matches SET status = 'finished' WHERE winner_reg_id IS NOT NULL AND status = 'pending'")
        )
        if "match_order" not in existing:
            conn.execute(text("ALTER TABLE bracket_matches ADD COLUMN match_order INT NOT NULL DEFAULT 0"))
        if "bracket_round_key" not in existing:
            conn.execute(text("ALTER TABLE bracket_matches ADD COLUMN bracket_round_key VARCHAR(32) NULL"))
        if "bracket_position" not in existing:
            conn.execute(text("ALTER TABLE bracket_matches ADD COLUMN bracket_position INT NULL"))


def ensure_bracket_match_sets_table() -> None:
    insp = inspect(engine)
    if insp.has_table("bracket_match_sets"):
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE bracket_match_sets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    match_id INT NOT NULL,
                    set_number INT NOT NULL,
                    reg1_score INT NOT NULL,
                    reg2_score INT NOT NULL,
                    CONSTRAINT fk_bracket_match_sets_match
                        FOREIGN KEY (match_id) REFERENCES bracket_matches(id) ON DELETE CASCADE,
                    CONSTRAINT uq_bracket_match_set_num UNIQUE (match_id, set_number)
                )
                """
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
