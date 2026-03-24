import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.registration import TournamentRegistration
    from app.models.match import BracketMatch


class GameFormat(str, enum.Enum):
    singles = "singles"
    doubles = "doubles"


class BracketFormat(str, enum.Enum):
    knockout = "knockout"
    group_knockout = "group_knockout"


class TournamentStatus(str, enum.Enum):
    draft = "draft"
    registration_open = "registration_open"
    registration_closed = "registration_closed"
    in_progress = "in_progress"
    completed = "completed"


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_format: Mapped[GameFormat] = mapped_column(SAEnum(GameFormat), default=GameFormat.singles)
    bracket_format: Mapped[BracketFormat] = mapped_column(SAEnum(BracketFormat), default=BracketFormat.knockout)
    max_participants: Mapped[int] = mapped_column(Integer, default=32)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[TournamentStatus] = mapped_column(SAEnum(TournamentStatus), default=TournamentStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizer: Mapped["User"] = relationship("User", back_populates="tournaments_organized")
    registrations: Mapped[list["TournamentRegistration"]] = relationship(
        "TournamentRegistration", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches: Mapped[list["BracketMatch"]] = relationship("BracketMatch", back_populates="tournament", cascade="all, delete-orphan")
