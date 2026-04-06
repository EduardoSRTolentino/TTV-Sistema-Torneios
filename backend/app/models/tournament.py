import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, JSON, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.registration import TournamentRegistration
    from app.models.match import BracketMatch
    from app.models.tournament_group import TournamentGroup


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
    registration_fee: Mapped[float] = mapped_column(Float, default=0.0)
    prize: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    match_best_of_sets: Mapped[int] = mapped_column(Integer, default=3)
    match_points_per_set: Mapped[int] = mapped_column(Integer, default=11)
    dispute_third_place: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_premiacao: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Fase de grupos (quando bracket_format == group_knockout)
    group_size: Mapped[int] = mapped_column(Integer, default=4)  # 3 ou 4
    number_of_groups: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = automático
    qualified_per_group: Mapped[int] = mapped_column(Integer, default=2)
    points_win: Mapped[int] = mapped_column(Integer, default=3)
    points_loss: Mapped[int] = mapped_column(Integer, default=0)
    tiebreak_criteria: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    auto_generate_groups_on_close: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[TournamentStatus] = mapped_column(SAEnum(TournamentStatus), default=TournamentStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizer: Mapped["User"] = relationship("User", back_populates="tournaments_organized")
    registrations: Mapped[list["TournamentRegistration"]] = relationship(
        "TournamentRegistration", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches: Mapped[list["BracketMatch"]] = relationship("BracketMatch", back_populates="tournament", cascade="all, delete-orphan")
    tournament_groups: Mapped[list["TournamentGroup"]] = relationship(
        "TournamentGroup", back_populates="tournament", cascade="all, delete-orphan", order_by="TournamentGroup.sort_order"
    )
