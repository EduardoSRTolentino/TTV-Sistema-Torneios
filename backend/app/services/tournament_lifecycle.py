"""Regras de estado: prazo de inscrição, encerramento e início do torneio."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.match import BracketMatch
from app.models.tournament import Tournament, TournamentStatus
from app.services.bracket import generate_knockout_bracket


def _deadline_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def auto_close_registrations_if_deadline_passed(db: Session, t: Tournament) -> bool:
    """Se inscrições estão abertas e o prazo já passou, fecha. Retorna True se alterou o status."""
    if t.status != TournamentStatus.registration_open:
        return False
    if not t.registration_deadline:
        return False
    dl = _deadline_utc(t.registration_deadline)
    if dl is None:
        return False
    if datetime.now(timezone.utc) <= dl:
        return False
    t.status = TournamentStatus.registration_closed
    return True


def apply_auto_close_to_tournaments(db: Session, tournaments: list[Tournament]) -> bool:
    """Aplica fechamento automático por prazo a uma lista de torneios já carregados. Faz commit se houver mudança."""
    changed = any(auto_close_registrations_if_deadline_passed(db, t) for t in tournaments)
    if changed:
        db.commit()
        for t in tournaments:
            db.refresh(t)
    return changed


def apply_auto_close_single(db: Session, t: Tournament) -> None:
    if auto_close_registrations_if_deadline_passed(db, t):
        db.commit()
        db.refresh(t)


def apply_manual_close_registrations(t: Tournament) -> None:
    """
    Encerra inscrições manualmente. Idempotente se já estiverem encerradas.
    Levanta ValueError se o estado não permitir.
    """
    if t.status == TournamentStatus.registration_open:
        t.status = TournamentStatus.registration_closed
        return
    if t.status == TournamentStatus.registration_closed:
        return
    if t.status == TournamentStatus.draft:
        raise ValueError("Abra as inscrições antes de encerrá-las.")
    raise ValueError("Não é possível encerrar inscrições: o torneio já está em andamento ou finalizado.")


def start_tournament(db: Session, t: Tournament) -> None:
    """
    Inicia o torneio: fecha inscrições se ainda estiverem abertas, gera chaveamento se necessário,
    define status em andamento. Não faz commit.
    Levanta ValueError em violações de regra ou na geração do chaveamento.
    """
    if t.status == TournamentStatus.completed:
        raise ValueError("Torneio já finalizado.")
    if t.status == TournamentStatus.in_progress:
        raise ValueError("Torneio já em andamento.")
    if t.status == TournamentStatus.draft:
        raise ValueError("Abra as inscrições antes de iniciar o torneio.")
    if t.status == TournamentStatus.registration_open:
        t.status = TournamentStatus.registration_closed
        db.flush()
    if t.status != TournamentStatus.registration_closed:
        raise ValueError("Estado inválido para iniciar o torneio.")

    n_matches = (
        db.query(func.count(BracketMatch.id)).filter(BracketMatch.tournament_id == t.id).scalar()
    )
    if int(n_matches or 0) > 0:
        t.status = TournamentStatus.in_progress
        db.flush()
        return

    generate_knockout_bracket(db, t)
    db.flush()
