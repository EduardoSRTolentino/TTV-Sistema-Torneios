"""Fase de grupos: geração (snake), partidas, classificação e passagem ao mata-mata."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.models.registration import TournamentRegistration
from app.models.tournament import BracketFormat, Tournament, TournamentStatus
from app.models.tournament_group import (
    GroupMatchStatus,
    TournamentGroup,
    TournamentGroupMatch,
    TournamentGroupMatchSet,
    TournamentGroupMember,
    TournamentGroupStanding,
)
from app.services.bracket import _order_registrations_by_seed, generate_knockout_bracket_from_registrations
from app.services.group_ranking import MatchLite, StandingAgg, build_stats_from_matches, rank_registrations
from app.services.match_service import SET_MIN_LEAD, SetScoreRow, infer_winner_registration_id_from_set_rows


def _tiebreak_list(t: Tournament) -> List[str]:
    raw = t.tiebreak_criteria
    if isinstance(raw, list) and raw:
        return [str(x) for x in raw]
    return list(DEFAULT_TIEBREAK_CRITERIA)


def _group_letter(idx: int) -> str:
    s = ""
    n = idx
    while True:
        s = chr(ord("A") + (n % 26)) + s
        n = n // 26 - 1
        if n < 0:
            break
    return s


def compute_num_groups(num_registrations: int, group_size: int, override: Optional[int]) -> int:
    if override is not None:
        return max(1, override)
    if num_registrations <= 0:
        return 1
    return max(1, math.ceil(num_registrations / group_size))


def snake_assign(reg_ids_ordered: Sequence[int], num_groups: int) -> List[List[int]]:
    groups: List[List[int]] = [[] for _ in range(num_groups)]
    idx = 0
    row = 0
    reg_ids_ordered = list(reg_ids_ordered)
    while idx < len(reg_ids_ordered):
        order = range(num_groups) if row % 2 == 0 else range(num_groups - 1, -1, -1)
        for g in order:
            if idx < len(reg_ids_ordered):
                groups[g].append(reg_ids_ordered[idx])
                idx += 1
        row += 1
    return groups


def _ordered_registrations(db: Session, tournament: Tournament) -> List[TournamentRegistration]:
    regs = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament.id)
        .all()
    )
    _order_registrations_by_seed(db, tournament, regs)
    return regs


def _initial_seed_map(ordered_regs: Sequence[TournamentRegistration]) -> Dict[int, int]:
    return {reg.id: i + 1 for i, reg in enumerate(ordered_regs)}


def groups_exist(db: Session, tournament_id: int) -> bool:
    n = db.query(TournamentGroup).filter(TournamentGroup.tournament_id == tournament_id).count()
    return int(n or 0) > 0


def assert_can_generate_groups(db: Session, tournament: Tournament) -> None:
    if tournament.bracket_format != BracketFormat.group_knockout:
        raise ValueError("Este torneio não está no formato grupos + mata-mata.")
    if tournament.status not in (
        TournamentStatus.registration_closed,
        TournamentStatus.in_progress,
    ):
        raise ValueError("Encerre as inscrições antes de gerar os grupos.")
    if groups_exist(db, tournament.id):
        raise ValueError("Os grupos já foram gerados.")
    n = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament.id)
        .count()
    )
    if int(n or 0) < 2:
        raise ValueError("São necessárias pelo menos 2 inscrições.")


def generate_groups(db: Session, tournament: Tournament) -> List[TournamentGroup]:
    assert_can_generate_groups(db, tournament)
    if tournament.group_size not in (3, 4):
        raise ValueError("group_size deve ser 3 ou 4.")

    ordered_regs = _ordered_registrations(db, tournament)
    seed_map = _initial_seed_map(ordered_regs)
    reg_ids = [r.id for r in ordered_regs]
    n = len(reg_ids)

    num_groups = compute_num_groups(n, tournament.group_size, tournament.number_of_groups)
    buckets = snake_assign(reg_ids, num_groups)
    min_bucket = min((len(b) for b in buckets if b), default=0)
    if min_bucket > 0 and tournament.qualified_per_group > min_bucket:
        raise ValueError(
            f"Classificados por grupo ({tournament.qualified_per_group}) excede o menor grupo ({min_bucket})."
        )

    created: List[TournamentGroup] = []
    for gi, bucket in enumerate(buckets):
        if not bucket:
            continue
        g = TournamentGroup(
            tournament_id=tournament.id,
            name=_group_letter(gi),
            sort_order=gi,
        )
        db.add(g)
        db.flush()
        for rid in bucket:
            db.add(TournamentGroupMember(group_id=g.id, registration_id=rid))
            db.add(
                TournamentGroupStanding(
                    group_id=g.id,
                    registration_id=rid,
                    initial_seed_rank=seed_map[rid],
                )
            )
        db.flush()
        _create_round_robin_matches(db, tournament, g, bucket)
        created.append(g)

    db.flush()
    for g in created:
        rebuild_standings_for_group(db, tournament, g.id)
    return created


def _create_round_robin_matches(
    db: Session,
    tournament: Tournament,
    group: TournamentGroup,
    registration_ids: Sequence[int],
) -> None:
    pairs: List[Tuple[int, int]] = []
    regs = list(registration_ids)
    for i in range(len(regs)):
        for j in range(i + 1, len(regs)):
            pairs.append((regs[i], regs[j]))
    mo = 1
    for a, b in pairs:
        m = TournamentGroupMatch(
            group_id=group.id,
            reg1_id=a,
            reg2_id=b,
            winner_reg_id=None,
            status=GroupMatchStatus.pending,
            match_order=mo,
        )
        mo += 1
        db.add(m)
    db.flush()


def _match_to_lite(
    m: TournamentGroupMatch,
    sets: Sequence[TournamentGroupMatchSet],
) -> MatchLite:
    r1s = r2s = 0
    for s in sets:
        if s.reg1_score > s.reg2_score:
            r1s += 1
        else:
            r2s += 1
    return MatchLite(
        reg1_id=m.reg1_id,
        reg2_id=m.reg2_id,
        winner_reg_id=m.winner_reg_id,
        reg1_sets_won=r1s,
        reg2_sets_won=r2s,
        reg1_points=sum(s.reg1_score for s in sets),
        reg2_points=sum(s.reg2_score for s in sets),
    )


def rebuild_standings_for_group(db: Session, tournament: Tournament, group_id: int) -> None:
    g = db.query(TournamentGroup).filter(TournamentGroup.id == group_id).first()
    if not g:
        return
    members = (
        db.query(TournamentGroupMember)
        .filter(TournamentGroupMember.group_id == group_id)
        .all()
    )
    reg_ids = [m.registration_id for m in members]
    matches = (
        db.query(TournamentGroupMatch)
        .filter(
            TournamentGroupMatch.group_id == group_id,
            TournamentGroupMatch.status.in_(
                (GroupMatchStatus.finished, GroupMatchStatus.walkover)
            ),
        )
        .all()
    )
    lites: List[MatchLite] = []
    for m in matches:
        sets = (
            db.query(TournamentGroupMatchSet)
            .filter(TournamentGroupMatchSet.match_id == m.id)
            .order_by(TournamentGroupMatchSet.set_number)
            .all()
        )
        lites.append(_match_to_lite(m, sets))

    agg = build_stats_from_matches(set(reg_ids), lites, tournament.points_win, tournament.points_loss)
    st_rows = (
        db.query(TournamentGroupStanding)
        .filter(TournamentGroupStanding.group_id == group_id)
        .all()
    )
    by_reg = {s.registration_id: s for s in st_rows}
    initial_rank = {s.registration_id: s.initial_seed_rank for s in st_rows}

    for rid in reg_ids:
        row = by_reg.get(rid)
        if row is None:
            continue
        a = agg.get(rid, StandingAgg())
        row.points = a.points
        row.wins = a.wins
        row.losses = a.losses
        row.sets_won = a.sets_won
        row.sets_lost = a.sets_lost
        row.points_scored = a.points_scored
        row.points_conceded = a.points_conceded

    order = rank_registrations(
        reg_ids,
        agg,
        lites,
        _tiebreak_list(tournament),
        initial_rank,
        tournament.points_win,
        tournament.points_loss,
    )
    pos = {rid: i + 1 for i, rid in enumerate(order)}
    for rid in reg_ids:
        if rid in by_reg:
            by_reg[rid].rank_position = pos.get(rid, 0)
    db.flush()


def all_group_matches_finished(db: Session, tournament_id: int) -> bool:
    pending = (
        db.query(TournamentGroupMatch)
        .join(TournamentGroup, TournamentGroup.id == TournamentGroupMatch.group_id)
        .filter(
            TournamentGroup.tournament_id == tournament_id,
            TournamentGroupMatch.status == GroupMatchStatus.pending,
        )
        .count()
    )
    return int(pending or 0) == 0


def build_qualifier_registration_ids(db: Session, tournament: Tournament) -> List[int]:
    qpg = tournament.qualified_per_group
    groups = (
        db.query(TournamentGroup)
        .filter(TournamentGroup.tournament_id == tournament.id)
        .order_by(TournamentGroup.sort_order)
        .all()
    )
    out: List[int] = []
    for rank in range(1, qpg + 1):
        for g in groups:
            st = (
                db.query(TournamentGroupStanding)
                .filter(
                    TournamentGroupStanding.group_id == g.id,
                    TournamentGroupStanding.rank_position == rank,
                )
                .first()
            )
            if st:
                out.append(st.registration_id)
    return out


def generate_knockout_from_groups_phase(db: Session, tournament: Tournament) -> None:
    if tournament.bracket_format != BracketFormat.group_knockout:
        raise ValueError("Torneio não é grupos + mata-mata.")
    if not groups_exist(db, tournament.id):
        raise ValueError("Gere os grupos antes do mata-mata.")
    if not all_group_matches_finished(db, tournament.id):
        raise ValueError("Finalize todas as partidas de grupo antes do mata-mata.")
    from app.models.match import BracketMatch

    if int(db.query(BracketMatch).filter(BracketMatch.tournament_id == tournament.id).count() or 0) > 0:
        raise ValueError("O mata-mata já foi gerado.")

    ordered = build_qualifier_registration_ids(db, tournament)
    if len(ordered) < 2:
        raise ValueError("Classificados insuficientes para o mata-mata.")

    generate_knockout_bracket_from_registrations(
        db, tournament, ordered, set_status_in_progress=False
    )


def submit_group_match_sets(
    db: Session,
    tournament: Tournament,
    m: TournamentGroupMatch,
    sets: List[SetScoreRow],
) -> TournamentGroupMatch:
    if tournament.status != TournamentStatus.in_progress:
        raise ValueError("Torneio não está em andamento.")
    if m.status != GroupMatchStatus.pending:
        raise ValueError("Partida já finalizada.")
    wid = infer_winner_registration_id_from_set_rows(
        m.reg1_id,
        m.reg2_id,
        sets,
        tournament.match_best_of_sets,
        tournament.match_points_per_set,
        SET_MIN_LEAD,
    )
    db.query(TournamentGroupMatchSet).filter(TournamentGroupMatchSet.match_id == m.id).delete(
        synchronize_session=False
    )
    for row in sorted(sets, key=lambda s: s.set_number):
        db.add(
            TournamentGroupMatchSet(
                match_id=m.id,
                set_number=row.set_number,
                reg1_score=row.reg1_score,
                reg2_score=row.reg2_score,
            )
        )
    m.winner_reg_id = wid
    m.status = GroupMatchStatus.finished
    db.flush()
    rebuild_standings_for_group(db, tournament, m.group_id)
    return m


def apply_group_walkover(
    db: Session,
    tournament: Tournament,
    m: TournamentGroupMatch,
    winner_registration_id: int,
) -> TournamentGroupMatch:
    if tournament.status != TournamentStatus.in_progress:
        raise ValueError("Torneio não está em andamento.")
    if m.status != GroupMatchStatus.pending:
        raise ValueError("Partida já finalizada.")
    if winner_registration_id not in (m.reg1_id, m.reg2_id):
        raise ValueError("Vencedor inválido.")
    need = (tournament.match_best_of_sets + 1) // 2
    db.query(TournamentGroupMatchSet).filter(TournamentGroupMatchSet.match_id == m.id).delete(
        synchronize_session=False
    )
    for i in range(need):
        db.add(
            TournamentGroupMatchSet(
                match_id=m.id,
                set_number=i + 1,
                reg1_score=11 if winner_registration_id == m.reg1_id else 0,
                reg2_score=11 if winner_registration_id == m.reg2_id else 0,
            )
        )
    m.winner_reg_id = winner_registration_id
    m.status = GroupMatchStatus.walkover
    db.flush()
    rebuild_standings_for_group(db, tournament, m.group_id)
    return m


def _rebuild_group_members_and_matches(
    db: Session,
    tournament: Tournament,
    group: TournamentGroup,
    registration_ids: Sequence[int],
) -> None:
    db.query(TournamentGroupMatch).filter(TournamentGroupMatch.group_id == group.id).delete(
        synchronize_session=False
    )
    db.query(TournamentGroupStanding).filter(TournamentGroupStanding.group_id == group.id).delete(
        synchronize_session=False
    )
    db.query(TournamentGroupMember).filter(TournamentGroupMember.group_id == group.id).delete(
        synchronize_session=False
    )
    db.flush()
    ordered_regs = _ordered_registrations(db, tournament)
    seed_map = _initial_seed_map(ordered_regs)
    for rid in registration_ids:
        db.add(TournamentGroupMember(group_id=group.id, registration_id=rid))
        db.add(
            TournamentGroupStanding(
                group_id=group.id,
                registration_id=rid,
                initial_seed_rank=seed_map.get(rid, 999),
            )
        )
    db.flush()
    _create_round_robin_matches(db, tournament, group, registration_ids)


def move_registration_to_group(
    db: Session,
    tournament: Tournament,
    registration_id: int,
    target_group_id: int,
) -> None:
    if tournament.status != TournamentStatus.in_progress:
        raise ValueError("Só é possível mover com o torneio em andamento.")
    fin = (
        db.query(TournamentGroupMatch)
        .join(TournamentGroup, TournamentGroup.id == TournamentGroupMatch.group_id)
        .filter(
            TournamentGroup.tournament_id == tournament.id,
            TournamentGroupMatch.status != GroupMatchStatus.pending,
        )
        .count()
    )
    if int(fin or 0) > 0:
        raise ValueError("Não é possível mover após partidas já disputadas.")

    mem = (
        db.query(TournamentGroupMember)
        .filter(TournamentGroupMember.registration_id == registration_id)
        .join(TournamentGroup, TournamentGroup.id == TournamentGroupMember.group_id)
        .filter(TournamentGroup.tournament_id == tournament.id)
        .first()
    )
    if not mem:
        raise ValueError("Inscrição não está em nenhum grupo.")
    old_gid = mem.group_id
    tgt = db.query(TournamentGroup).filter(TournamentGroup.id == target_group_id).first()
    if not tgt or tgt.tournament_id != tournament.id:
        raise ValueError("Grupo de destino inválido.")
    if old_gid == target_group_id:
        return

    src_group = db.query(TournamentGroup).filter(TournamentGroup.id == old_gid).first()
    if not src_group:
        return

    src_regs = [
        m.registration_id
        for m in db.query(TournamentGroupMember)
        .filter(TournamentGroupMember.group_id == old_gid)
        .all()
        if m.registration_id != registration_id
    ]
    tgt_regs = [
        m.registration_id
        for m in db.query(TournamentGroupMember)
        .filter(TournamentGroupMember.group_id == target_group_id)
        .all()
    ]
    tgt_regs = [r for r in tgt_regs if r != registration_id]
    tgt_regs.append(registration_id)

    _rebuild_group_members_and_matches(db, tournament, src_group, src_regs)
    _rebuild_group_members_and_matches(db, tournament, tgt, tgt_regs)
