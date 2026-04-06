"""Fase de grupos (round-robin) antes do mata-mata."""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.registration import TournamentRegistration


class GroupMatchStatus(str, enum.Enum):
    pending = "pending"
    finished = "finished"
    walkover = "walkover"


class TournamentGroup(Base):
    __tablename__ = "tournament_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(8))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    tournament = relationship("Tournament", back_populates="tournament_groups")
    members = relationship(
        "TournamentGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="TournamentGroupMember.id",
    )
    matches = relationship(
        "TournamentGroupMatch",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="TournamentGroupMatch.match_order",
    )
    standings = relationship(
        "TournamentGroupStanding",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="TournamentGroupStanding.rank_position",
    )


class TournamentGroupMember(Base):
    __tablename__ = "tournament_group_members"
    __table_args__ = (UniqueConstraint("group_id", "registration_id", name="uq_group_member_reg"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tournament_groups.id", ondelete="CASCADE"))
    registration_id: Mapped[int] = mapped_column(ForeignKey("tournament_registrations.id", ondelete="CASCADE"))

    group = relationship("TournamentGroup", back_populates="members")
    registration = relationship("TournamentRegistration")


class TournamentGroupMatch(Base):
    __tablename__ = "tournament_group_matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tournament_groups.id", ondelete="CASCADE"))
    reg1_id: Mapped[int] = mapped_column(ForeignKey("tournament_registrations.id"))
    reg2_id: Mapped[int] = mapped_column(ForeignKey("tournament_registrations.id"))
    winner_reg_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournament_registrations.id"), nullable=True)
    status: Mapped[GroupMatchStatus] = mapped_column(
        SAEnum(GroupMatchStatus, values_callable=lambda e: [m.value for m in e]),
        default=GroupMatchStatus.pending,
    )
    match_order: Mapped[int] = mapped_column(Integer, default=0)

    group = relationship("TournamentGroup", back_populates="matches")
    sets = relationship(
        "TournamentGroupMatchSet",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="TournamentGroupMatchSet.set_number",
    )


class TournamentGroupMatchSet(Base):
    __tablename__ = "tournament_group_match_sets"
    __table_args__ = (UniqueConstraint("match_id", "set_number", name="uq_group_match_set_num"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("tournament_group_matches.id", ondelete="CASCADE"))
    set_number: Mapped[int] = mapped_column(Integer)
    reg1_score: Mapped[int] = mapped_column(Integer)
    reg2_score: Mapped[int] = mapped_column(Integer)

    match = relationship("TournamentGroupMatch", back_populates="sets")


class TournamentGroupStanding(Base):
    __tablename__ = "tournament_group_standings"
    __table_args__ = (UniqueConstraint("group_id", "registration_id", name="uq_group_standing_reg"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tournament_groups.id", ondelete="CASCADE"))
    registration_id: Mapped[int] = mapped_column(ForeignKey("tournament_registrations.id", ondelete="CASCADE"))
    points: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    sets_won: Mapped[int] = mapped_column(Integer, default=0)
    sets_lost: Mapped[int] = mapped_column(Integer, default=0)
    points_scored: Mapped[int] = mapped_column(Integer, default=0)
    points_conceded: Mapped[int] = mapped_column(Integer, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, default=0)
    initial_seed_rank: Mapped[int] = mapped_column(Integer, default=0)  # 1 = melhor no torneio (pré-grupos)

    group = relationship("TournamentGroup", back_populates="standings")
