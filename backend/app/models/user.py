import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    organizer = "organizer"
    player = "player"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.player)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tournaments_organized = relationship("Tournament", back_populates="organizer")
    registrations = relationship("TournamentRegistration", back_populates="user", foreign_keys="TournamentRegistration.user_id")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
