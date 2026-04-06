"""Geração de chaveamento mata-mata com seeding por ranking e BYEs para os melhores seeds."""
from __future__ import annotations

import math
import random
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.elo import EloRating
from app.models.match import BracketMatch
from app.models.registration import TournamentRegistration
from app.models.tournament import GameFormat, Tournament, TournamentStatus
from app.services.match_flow import propagate_initial_bye_winners


def _next_power_of_2(n: int) -> int:
    if n <= 1:
        return 1
    p = 1
    while p < n:
        p <<= 1
    return p


def _user_rating(db: Session, user_id: int) -> float:
    elo = db.query(EloRating).filter(EloRating.user_id == user_id).first()
    return float(elo.rating) if elo else 1500.0


def compute_registration_seed_rating(db: Session, tournament: Tournament, reg: TournamentRegistration) -> float:
    r_main = _user_rating(db, reg.user_id)
    if tournament.game_format == GameFormat.doubles:
        if reg.partner_user_id is None:
            raise ValueError("Inscrição em duplas sem parceiro definido.")
        r_partner = _user_rating(db, reg.partner_user_id)
        return (r_main + r_partner) / 2.0
    return r_main


def _order_registrations_by_seed(db: Session, tournament: Tournament, regs: list[TournamentRegistration]) -> None:
    """Ordena por ranking (maior primeiro), empatando com embaralhamento; congela bracket_seed_rating."""
    scored = [(reg, compute_registration_seed_rating(db, tournament, reg)) for reg in regs]
    scored.sort(key=lambda x: -x[1])
    i = 0
    n = len(scored)
    ordered: list[TournamentRegistration] = []
    while i < n:
        j = i
        while j + 1 < n and scored[j + 1][1] == scored[i][1]:
            j += 1
        group = [scored[k][0] for k in range(i, j + 1)]
        random.shuffle(group)
        ordered.extend(group)
        i = j + 1
    rating_by_id = {reg.id: rt for reg, rt in scored}
    for reg in ordered:
        reg.bracket_seed_rating = rating_by_id[reg.id]
    regs.clear()
    regs.extend(ordered)


def compute_first_round_slots(n: int, ordered_registration_ids: list[int]) -> list[Optional[int]]:
    """
    n participantes; IDs na ordem seed 1..n (melhor → pior).
    Chave S = próxima potência de 2: confrontos 1 vs S, 2 vs S-1, …; seeds inexistentes viram BYE.
    """
    if len(ordered_registration_ids) != n:
        raise ValueError("Lista de inscrições não bate com n.")
    S = _next_power_of_2(n)

    def reg_id_for_seed(seed_num: int) -> Optional[int]:
        if 1 <= seed_num <= n:
            return ordered_registration_ids[seed_num - 1]
        return None

    slots: list[Optional[int]] = []
    for i in range(S // 2):
        a = i + 1
        b = S - i
        slots.append(reg_id_for_seed(a))
        slots.append(reg_id_for_seed(b))
    return slots


def generate_knockout_bracket(db: Session, tournament: Tournament) -> List[BracketMatch]:
    regs = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament.id)
        .all()
    )
    if len(regs) < 2:
        raise ValueError("É necessário pelo menos 2 inscrições para gerar o chaveamento.")

    _order_registrations_by_seed(db, tournament, regs)

    db.query(BracketMatch).filter(BracketMatch.tournament_id == tournament.id).delete()
    db.flush()

    reg_ids = compute_first_round_slots(len(regs), [r.id for r in regs])
    size = len(reg_ids)
    num_rounds = int(math.log2(size))

    round_matches: dict[int, list[BracketMatch]] = {}
    for r in range(num_rounds, 0, -1):
        num_matches = 2 ** (num_rounds - r)
        round_matches[r] = []
        for pos in range(num_matches):
            next_id = None
            if r < num_rounds:
                parent = round_matches[r + 1][pos // 2]
                next_id = parent.id
            m = BracketMatch(
                tournament_id=tournament.id,
                round_number=r,
                position_in_round=pos,
                next_match_id=next_id,
            )
            db.add(m)
            db.flush()
            round_matches[r].append(m)

    r1_matches = round_matches[1]
    for i, m in enumerate(r1_matches):
        a, b = reg_ids[2 * i], reg_ids[2 * i + 1]
        m.reg1_id = a
        m.reg2_id = b
        if a is None and b is None:
            continue
        if a is None:
            m.winner_reg_id = b
        elif b is None:
            m.winner_reg_id = a

    db.flush()
    propagate_initial_bye_winners(db, r1_matches)
    db.flush()

    tournament.status = TournamentStatus.in_progress
    db.flush()
    return [m for r in sorted(round_matches.keys()) for m in round_matches[r]]
