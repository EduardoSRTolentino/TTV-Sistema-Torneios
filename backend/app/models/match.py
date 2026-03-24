from typing import Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BracketMatch(Base):
    """Partida do mata-mata: jogadores identificados pelas inscrições (time em duplas)."""
    __tablename__ = "bracket_matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    round_number: Mapped[int] = mapped_column(Integer)  # 1 = primeira rodada (mais jogos)
    position_in_round: Mapped[int] = mapped_column(Integer)
    reg1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    reg2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    winner_reg_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    next_match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bracket_matches.id"), nullable=True)

    tournament = relationship("Tournament", back_populates="matches")
