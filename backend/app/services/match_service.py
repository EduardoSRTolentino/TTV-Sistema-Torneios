"""Validação de sets, registro de placar e finalização de partidas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from sqlalchemy.orm import Session

from app.models.match import BracketMatch, BracketMatchSet, BracketMatchStatus
from app.models.tournament import Tournament, TournamentStatus
from app.services.match_flow import set_match_winner

# Diferença mínima de pontos para vencer um set (regra fixa do tênis de mesa).
SET_MIN_LEAD = 2


def is_valid_terminal_set(score_a: int, score_b: int, points_per_set: int, min_lead: int = SET_MIN_LEAD) -> bool:
    """Set terminado: vencedor com pelo menos `points_per_set` pontos e vantagem >= min_lead (inclui deuce)."""
    if score_a < 0 or score_b < 0 or score_a == score_b:
        return False
    hi, lo = max(score_a, score_b), min(score_a, score_b)
    diff = hi - lo
    if diff < min_lead:
        return False
    if hi < points_per_set:
        return False
    if lo >= points_per_set - 1:
        return True
    return hi == points_per_set and diff >= min_lead


@dataclass(frozen=True)
class SetScoreRow:
    set_number: int
    reg1_score: int
    reg2_score: int


def infer_winner_registration_id_from_sets(
    match: BracketMatch,
    sets: Sequence[SetScoreRow],
    best_of_sets: int,
    points_per_set: int,
    min_lead: int = SET_MIN_LEAD,
) -> int:
    """
    Valida cada set e a sequência (sem sets extras após decisão).
    Retorna o registration_id do vencedor (reg1 ou reg2).
    """
    if match.reg1_id is None or match.reg2_id is None:
        raise ValueError("Partida sem dois jogadores definidos (BYE não recebe placar por sets).")
    if match.reg1_id == match.reg2_id:
        raise ValueError("Inscrições duplicadas na mesma partida.")
    if not sets:
        raise ValueError("Informe pelo menos um set.")
    ordered = sorted(sets, key=lambda s: s.set_number)
    nums = [s.set_number for s in ordered]
    if len(set(nums)) != len(nums):
        raise ValueError("Número de set repetido.")
    if any(n < 1 for n in nums):
        raise ValueError("Número de set inválido.")
    need = (best_of_sets + 1) // 2
    w1 = w2 = 0
    for i, row in enumerate(ordered):
        if not is_valid_terminal_set(row.reg1_score, row.reg2_score, points_per_set, min_lead):
            raise ValueError(
                f"Set {row.set_number} inválido: placar não fecha com {points_per_set} pontos e diferença mínima {min_lead}."
            )
        if row.reg1_score > row.reg2_score:
            w1 += 1
        else:
            w2 += 1
        if w1 >= need or w2 >= need:
            if i != len(ordered) - 1:
                raise ValueError("Não envie sets após o vencedor da partida já estar decidido.")
            break
    else:
        raise ValueError("Resultado incompleto: nenhum jogador atingiu os sets necessários para vencer.")
    if w1 >= need and w2 >= need:
        raise ValueError("Placar inconsistente: ambos venceriam a partida.")
    if w1 >= need:
        return match.reg1_id
    return match.reg2_id


def submit_match_set_scores(
    db: Session,
    tournament: Tournament,
    match: BracketMatch,
    sets: List[SetScoreRow],
) -> BracketMatch:
    if tournament.status != TournamentStatus.in_progress:
        raise ValueError("Só é possível registrar resultado com o torneio em andamento.")
    if match.tournament_id != tournament.id:
        raise ValueError("Partida não pertence a este torneio.")
    if match.status == BracketMatchStatus.finished:
        raise ValueError("Partida já finalizada.")
    winner_id = infer_winner_registration_id_from_sets(
        match,
        sets,
        tournament.match_best_of_sets,
        tournament.match_points_per_set,
        SET_MIN_LEAD,
    )
    db.query(BracketMatchSet).filter(BracketMatchSet.match_id == match.id).delete(synchronize_session=False)
    for row in sorted(sets, key=lambda s: s.set_number):
        db.add(
            BracketMatchSet(
                match_id=match.id,
                set_number=row.set_number,
                reg1_score=row.reg1_score,
                reg2_score=row.reg2_score,
            )
        )
    db.flush()
    set_match_winner(db, match, winner_id)
    return match
