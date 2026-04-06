"""Serialização da fase de grupos para a API."""
from __future__ import annotations

from collections import defaultdict
from typing import List

from sqlalchemy.orm import Session

from app.models.registration import TournamentRegistration
from app.models.tournament import GameFormat, Tournament
from app.models.tournament_group import TournamentGroup, TournamentGroupMatch, TournamentGroupMatchSet
from app.models.user import User
from app.schemas.groups import GroupDetailOut, GroupMatchOut, GroupMatchSetOut, GroupsPhaseOut, GroupStandingOut


def _reg_label(db: Session, reg: TournamentRegistration, game_format: GameFormat) -> str:
    u1 = db.query(User).filter(User.id == reg.user_id).first()
    n1 = u1.full_name if u1 else f"#{reg.user_id}"
    if game_format == GameFormat.doubles and reg.partner_user_id:
        u2 = db.query(User).filter(User.id == reg.partner_user_id).first()
        n2 = u2.full_name if u2 else f"#{reg.partner_user_id}"
        return f"{n1} + {n2}"
    return n1


def enrich_groups_phase(db: Session, tournament: Tournament) -> GroupsPhaseOut:
    groups = (
        db.query(TournamentGroup)
        .filter(TournamentGroup.tournament_id == tournament.id)
        .order_by(TournamentGroup.sort_order)
        .all()
    )
    if not groups:
        return GroupsPhaseOut(tournament_id=tournament.id, groups=[])

    reg_ids: set[int] = set()
    for g in groups:
        for m in g.members:
            reg_ids.add(m.registration_id)

    reg_map = {
        r.id: r
        for r in db.query(TournamentRegistration)
        .filter(TournamentRegistration.id.in_(list(reg_ids)))
        .all()
    }

    out_groups: List[GroupDetailOut] = []
    for g in groups:
        st_rows = sorted(g.standings, key=lambda s: (s.rank_position, s.registration_id))
        standings_out: List[GroupStandingOut] = []
        for s in st_rows:
            reg = reg_map.get(s.registration_id)
            disp = _reg_label(db, reg, tournament.game_format) if reg else f"#{s.registration_id}"
            standings_out.append(
                GroupStandingOut(
                    registration_id=s.registration_id,
                    display_name=disp,
                    points=s.points,
                    wins=s.wins,
                    losses=s.losses,
                    sets_won=s.sets_won,
                    sets_lost=s.sets_lost,
                    points_scored=s.points_scored,
                    points_conceded=s.points_conceded,
                    rank_position=s.rank_position,
                    initial_seed_rank=s.initial_seed_rank,
                )
            )

        match_ids = [m.id for m in g.matches]
        sets_by_match: dict[int, list[TournamentGroupMatchSet]] = defaultdict(list)
        if match_ids:
            set_rows = (
                db.query(TournamentGroupMatchSet)
                .filter(TournamentGroupMatchSet.match_id.in_(match_ids))
                .order_by(TournamentGroupMatchSet.match_id, TournamentGroupMatchSet.set_number)
                .all()
            )
            for s in set_rows:
                sets_by_match[s.match_id].append(s)

        matches_out: List[GroupMatchOut] = []
        for m in sorted(g.matches, key=lambda x: (x.match_order, x.id)):
            r1 = reg_map.get(m.reg1_id)
            r2 = reg_map.get(m.reg2_id)
            rw = reg_map.get(m.winner_reg_id) if m.winner_reg_id else None
            st_list = [
                GroupMatchSetOut(set_number=s.set_number, reg1_score=s.reg1_score, reg2_score=s.reg2_score)
                for s in sets_by_match.get(m.id, [])
            ]
            matches_out.append(
                GroupMatchOut(
                    id=m.id,
                    group_id=m.group_id,
                    reg1_id=m.reg1_id,
                    reg2_id=m.reg2_id,
                    winner_reg_id=m.winner_reg_id,
                    status=m.status.value,
                    match_order=m.match_order,
                    reg1_display=_reg_label(db, r1, tournament.game_format) if r1 else "?",
                    reg2_display=_reg_label(db, r2, tournament.game_format) if r2 else "?",
                    winner_display=_reg_label(db, rw, tournament.game_format) if rw else None,
                    sets=st_list,
                )
            )

        out_groups.append(
            GroupDetailOut(id=g.id, name=g.name, sort_order=g.sort_order, standings=standings_out, matches=matches_out)
        )

    return GroupsPhaseOut(tournament_id=tournament.id, groups=out_groups)
