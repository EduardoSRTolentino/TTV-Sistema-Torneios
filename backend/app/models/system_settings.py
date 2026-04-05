"""Configurações globais (singleton: uma única linha, id=1)."""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

SINGLETON_SETTINGS_ID = 1


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    initial_ranking: Mapped[int] = mapped_column(Integer, nullable=False)
