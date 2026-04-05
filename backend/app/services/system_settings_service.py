from sqlalchemy.orm import Session

from app.models.system_settings import SINGLETON_SETTINGS_ID, SystemSettings

DEFAULT_INITIAL_RANKING = 1000


def get_initial_ranking_int(db: Session) -> int:
    row = db.query(SystemSettings).filter(SystemSettings.id == SINGLETON_SETTINGS_ID).first()
    if row is None:
        return DEFAULT_INITIAL_RANKING
    return int(row.initial_ranking)


def get_initial_ranking_float(db: Session) -> float:
    return float(get_initial_ranking_int(db))


def get_settings_for_api(db: Session) -> SystemSettings:
    """Retorna o registro singleton; se não existir, objeto lógico com valores padrão (sem persistir)."""
    row = db.query(SystemSettings).filter(SystemSettings.id == SINGLETON_SETTINGS_ID).first()
    if row is not None:
        return row
    return SystemSettings(id=SINGLETON_SETTINGS_ID, initial_ranking=DEFAULT_INITIAL_RANKING)


def upsert_initial_ranking(db: Session, initial_ranking: int) -> SystemSettings:
    row = db.query(SystemSettings).filter(SystemSettings.id == SINGLETON_SETTINGS_ID).first()
    if row is None:
        row = SystemSettings(id=SINGLETON_SETTINGS_ID, initial_ranking=initial_ranking)
        db.add(row)
    else:
        row.initial_ranking = initial_ranking
    db.flush()
    return row
