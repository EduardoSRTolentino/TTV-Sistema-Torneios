"""Geração de chaveamento mata-mata com seeding competitivo (1º × último na ponta, BYEs para melhores seeds)."""
from __future__ import annotations

import math
import random
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.elo import EloRating
from app.models.match import BracketMatch, BracketMatchKind, BracketMatchStatus
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


def standard_bracket_seed_line(n: int) -> list[int]:
    """
    Linha do bracket (folhas) com seeds 1..n, n potência de 2.
    Expansão padrão: garante 1º e 2º só na final, 1º e 3º só na semi, etc.
    Ex.: n=8 → [1, 8, 4, 5, 2, 7, 3, 6] (pares consecutivos = confrontos).
    """
    if n < 1:
        return []
    if n == 1:
        return [1]
    r = 1
    seeds = [1]
    while len(seeds) < n:
        nxt: list[int] = []
        for s in seeds:
            nxt.append(s)
            nxt.append(2**r + 1 - s)
        seeds = nxt
        r += 1
    return seeds


def competitive_bracket_seed_line(n: int) -> list[int]:
    """
    Ordem das folhas alinhada ao padrão desejado (ex. 8 jogadores):
    [1, 8, 4, 5, 3, 6, 2, 7] — mesmos confrontos que o padrão, metade direita reordenada em blocos de 4.
    """
    seeds = standard_bracket_seed_line(n)
    if n <= 4:
        return seeds
    h = n // 2
    left = seeds[:h]
    right = seeds[h:]
    new_right: list[int] = []
    i = 0
    while i < len(right):
        if i + 4 <= len(right):
            chunk = right[i : i + 4]
            new_right.extend([chunk[2], chunk[3], chunk[0], chunk[1]])
            i += 4
        else:
            new_right.extend(right[i:])
            break
    return left + new_right


def first_round_schedule_permutation(num_matches: int) -> list[int]:
    """
    Permutação P: P[k] = índice da partida (0..num_matches-1) jogada na ordem k (0ª, 1ª, …).
    Intercala metades recursivamente: ex. 4 partidas → [0, 2, 1, 3] em ordem de jogo.
    """
    if num_matches < 1:
        return []
    if num_matches == 1:
        return [0]
    if num_matches == 2:
        return [0, 1]
    half = num_matches // 2
    left = first_round_schedule_permutation(half)
    right = [half + x for x in first_round_schedule_permutation(half)]
    out: list[int] = []
    for i in range(half):
        out.append(left[i])
        out.append(right[i])
    return out


def first_round_match_order_by_position(num_matches: int) -> list[int]:
    """Para cada position_in_round (0..n-1), valor match_order (1..n) na ordem de campanha."""
    perm = first_round_schedule_permutation(num_matches)
    inv = [0] * num_matches
    for order, pos in enumerate(perm):
        inv[pos] = order + 1
    return inv


def bracket_round_key(round_number: int, total_rounds: int) -> str:
    """Chave estável da fase (ex.: quarterfinal, semifinal, final)."""
    if total_rounds < 1:
        return f"round_{round_number}"
    d = total_rounds - round_number
    if d == 0:
        return "final"
    if d == 1:
        return "semifinal"
    if d == 2:
        return "quarterfinal"
    if d == 3:
        return "round_of_16"
    if d == 4:
        return "round_of_32"
    if d == 5:
        return "round_of_64"
    return f"round_of_{2 ** (d + 1)}"


def compute_first_round_slots(n: int, ordered_registration_ids: list[int]) -> list[Optional[int]]:
    """
    n participantes; IDs na ordem seed 1..n (melhor → pior).
    Folhas do bracket em ordem competitiva; seeds ausentes viram BYE no slot do oponente.
    """
    if len(ordered_registration_ids) != n:
        raise ValueError("Lista de inscrições não bate com n.")
    S = _next_power_of_2(n)
    line = competitive_bracket_seed_line(S)

    def reg_id_for_seed(seed_num: int) -> Optional[int]:
        if 1 <= seed_num <= n:
            return ordered_registration_ids[seed_num - 1]
        return None

    slots: list[Optional[int]] = []
    for s in line:
        slots.append(reg_id_for_seed(s))

    seen: set[int] = set()
    for x in slots:
        if x is not None:
            if x in seen:
                raise ValueError("Inscrição duplicada no chaveamento.")
            seen.add(x)
    return slots


def generate_knockout_bracket_from_registrations(
    db: Session,
    tournament: Tournament,
    ordered_registration_ids: list[int],
    *,
    set_status_in_progress: bool = True,
) -> List[BracketMatch]:
    """
    `ordered_registration_ids`: seed 1 = melhor … seed n = pior (ordenação já definida pelo chamador).
    """
    existing = (
        db.query(BracketMatch).filter(BracketMatch.tournament_id == tournament.id).count()
    )
    if int(existing or 0) > 0:
        raise ValueError("Chaveamento já existe. Não é possível gerar novamente.")

    n = len(ordered_registration_ids)
    if n < 2:
        raise ValueError("É necessário pelo menos 2 inscrições para gerar o chaveamento.")

    reg_ids = compute_first_round_slots(n, ordered_registration_ids)
    size = len(reg_ids)
    num_rounds = int(math.log2(size))
    r1_count = size // 2
    r1_orders = first_round_match_order_by_position(r1_count)

    round_matches: dict[int, list[BracketMatch]] = {}
    bracket_pos = 0
    for r in range(num_rounds, 0, -1):
        num_matches = 2 ** (num_rounds - r)
        round_matches[r] = []
        for pos in range(num_matches):
            next_id = None
            if r < num_rounds:
                parent = round_matches[r + 1][pos // 2]
                next_id = parent.id
            rk = bracket_round_key(r, num_rounds)
            mo = r1_orders[pos] if r == 1 else pos + 1
            m = BracketMatch(
                tournament_id=tournament.id,
                round_number=r,
                position_in_round=pos,
                next_match_id=next_id,
                status=BracketMatchStatus.pending,
                match_kind=BracketMatchKind.knockout,
                match_order=mo,
                bracket_round_key=rk,
                bracket_position=bracket_pos,
            )
            bracket_pos += 1
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
            m.status = BracketMatchStatus.finished
        elif b is None:
            m.winner_reg_id = a
            m.status = BracketMatchStatus.finished

    db.flush()
    propagate_initial_bye_winners(db, r1_matches)
    db.flush()

    if set_status_in_progress:
        tournament.status = TournamentStatus.in_progress
        db.flush()
    return [m for r in sorted(round_matches.keys()) for m in round_matches[r]]


def generate_knockout_bracket(db: Session, tournament: Tournament) -> List[BracketMatch]:
    regs = (
        db.query(TournamentRegistration)
        .filter(TournamentRegistration.tournament_id == tournament.id)
        .all()
    )
    if len(regs) < 2:
        raise ValueError("É necessário pelo menos 2 inscrições para gerar o chaveamento.")

    _order_registrations_by_seed(db, tournament, regs)

    return generate_knockout_bracket_from_registrations(
        db, tournament, [r.id for r in regs], set_status_in_progress=True
    )
