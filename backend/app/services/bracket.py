"""Geração de chaveamento mata-mata (MVP)."""
from __future__ import annotations

import math
import random
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.match import BracketMatch
from app.models.registration import TournamentRegistration
from app.models.tournament import Tournament, TournamentStatus


def _next_power_of_2(n: int) -> int:
    if n <= 1:
        return 1
    p = 1
    while p < n:
        p <<= 1
    return p


def generate_knockout_bracket(db: Session, tournament: Tournament) -> List[BracketMatch]:
    """
    Cria partidas de mata-mata com byes quando necessário.
    Ordem das inscrições é embaralhada (MVP).
    """
    regs = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament.id)
        .all()
    )
    if len(regs) < 2:
        raise ValueError("É necessário pelo menos 2 inscrições para gerar o chaveamento.")

    # Remove partidas antigas se existirem
    db.query(BracketMatch).filter(BracketMatch.tournament_id == tournament.id).delete()
    db.flush()

    reg_ids: List[Optional[int]] = [r.id for r in regs]
    random.shuffle(reg_ids)

    size = _next_power_of_2(len(reg_ids))
    while len(reg_ids) < size:
        reg_ids.append(None)

    num_rounds = int(math.log2(size))

    # Cria da final para a primeira rodada para encadear next_match_id
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

    # Preenche primeira rodada
    for i, m in enumerate(round_matches[1]):
        a, b = reg_ids[2 * i], reg_ids[2 * i + 1]
        m.reg1_id = a
        m.reg2_id = b
        if a is None and b is None:
            continue
        if a is None:
            m.winner_reg_id = b
        elif b is None:
            m.winner_reg_id = a

    tournament.status = TournamentStatus.in_progress
    db.flush()
    return [m for r in sorted(round_matches.keys()) for m in round_matches[r]]
