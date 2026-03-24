from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TournamentRegistration(Base):
    """Inscrição: simples (só user) ou dupla (user + parceiro)."""
    __tablename__ = "tournament_registrations"
    __table_args__ = (UniqueConstraint("tournament_id", "user_id", name="uq_reg_tournament_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    partner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tournament = relationship("Tournament", back_populates="registrations")
    user = relationship("User", foreign_keys=[user_id], back_populates="registrations")
    partner = relationship("User", foreign_keys=[partner_user_id])
