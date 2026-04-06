import enum
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BracketMatchStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    finished = "finished"


class BracketMatchKind(str, enum.Enum):
    knockout = "knockout"
    third_place = "third_place"


class BracketMatch(Base):
    """Partida do mata-mata: jogadores identificados pelas inscrições (time em duplas)."""
    __tablename__ = "bracket_matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    round_number: Mapped[int] = mapped_column(Integer)  # 1 = primeira rodada (mais jogos)
    position_in_round: Mapped[int] = mapped_column(Integer)
    match_order: Mapped[int] = mapped_column(Integer, default=0)  # ordem de exibição/jogo na rodada
    bracket_round_key: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bracket_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reg1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    reg2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    winner_reg_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    next_match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bracket_matches.id"), nullable=True)
    status: Mapped[BracketMatchStatus] = mapped_column(
        SAEnum(BracketMatchStatus, values_callable=lambda e: [m.value for m in e]),
        default=BracketMatchStatus.pending,
    )
    match_kind: Mapped[BracketMatchKind] = mapped_column(
        SAEnum(BracketMatchKind, values_callable=lambda e: [m.value for m in e]),
        default=BracketMatchKind.knockout,
    )

    tournament = relationship("Tournament", back_populates="matches")
    sets = relationship(
        "BracketMatchSet",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="BracketMatchSet.set_number",
    )


class BracketMatchSet(Base):
    """Placar de um set dentro de uma partida do chaveamento."""
    __tablename__ = "bracket_match_sets"
    __table_args__ = (UniqueConstraint("match_id", "set_number", name="uq_bracket_match_set_num"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("bracket_matches.id", ondelete="CASCADE"))
    set_number: Mapped[int] = mapped_column(Integer)
    reg1_score: Mapped[int] = mapped_column(Integer)
    reg2_score: Mapped[int] = mapped_column(Integer)

    match = relationship("BracketMatch", back_populates="sets")
