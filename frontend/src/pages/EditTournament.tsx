import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import * as api from "@/api/client";
import type { Tournament } from "@/api/types";
import { useAuth } from "@/context/AuthContext";

function toDatetimeLocalValue(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function apiDetailMessage(e: unknown): string | null {
  if (!isAxiosError(e)) return null;
  const d = e.response?.data as { detail?: unknown } | undefined;
  const detail = d?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((x: { msg?: string }) => x.msg).filter(Boolean);
    if (parts.length) return parts.join("; ");
  }
  return null;
}

export function EditTournament() {
  const { id } = useParams();
  const tid = Number(id);
  const nav = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [t, setT] = useState<Tournament | null>(null);
  const [title, setTitle] = useState("");
  const [maxParticipants, setMaxParticipants] = useState(32);
  const [prize, setPrize] = useState("");
  const [registrationFee, setRegistrationFee] = useState(0);
  const [deadline, setDeadline] = useState("");
  const [matchBestOf, setMatchBestOf] = useState(3);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canEdit = useMemo(() => {
    if (!user || !t) return false;
    return user.role === "admin" || (user.role === "organizer" && t.organizer_id === user.id);
  }, [user, t]);

  useEffect(() => {
    if (!id || Number.isNaN(tid)) {
      setLoadErr("Torneio inválido.");
      return;
    }
    if (authLoading) return;
    if (!user) {
      setLoadErr("Faça login para continuar.");
      return;
    }
    api
      .getTournament(tid)
      .then((tournament) => {
        setT(tournament);
        setTitle(tournament.title);
        setMaxParticipants(tournament.max_participants);
        setPrize(tournament.prize ?? "");
        setRegistrationFee(tournament.registration_fee ?? 0);
        setDeadline(toDatetimeLocalValue(tournament.registration_deadline));
        setMatchBestOf(tournament.match_best_of_sets ?? 3);
      })
      .catch(() => setLoadErr("Não foi possível carregar o torneio."));
  }, [id, tid, user, authLoading]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!t || !canEdit) return;
    setErr(null);
    const trimmed = title.trim();
    if (!trimmed) {
      setErr("Informe o nome do torneio.");
      return;
    }
    if (maxParticipants < t.registrations_count) {
      setErr(
        `O número de vagas não pode ser menor que o total de inscritos (${t.registrations_count}).`,
      );
      return;
    }
    if (registrationFee < 0 || Number.isNaN(registrationFee)) {
      setErr("O valor da inscrição deve ser zero ou positivo.");
      return;
    }
    setSaving(true);
    try {
      await api.updateTournament(t.id, {
        title: trimmed,
        max_participants: maxParticipants,
        prize: prize.trim() || null,
        registration_fee: registrationFee,
        registration_deadline: deadline ? new Date(deadline).toISOString() : null,
        match_best_of_sets: matchBestOf,
      });
      nav(`/torneios/${t.id}`);
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível salvar. Tente novamente.");
    } finally {
      setSaving(false);
    }
  }

  if (authLoading || (!loadErr && !t)) return <p>Carregando…</p>;
  if (loadErr) {
    return (
      <div className="page-narrow">
        <p className="error">{loadErr}</p>
        <p>
          <Link to={Number.isFinite(tid) ? `/torneios/${tid}` : "/torneios"}>Voltar</Link>
        </p>
      </div>
    );
  }
  if (!t || !canEdit) {
    return (
      <div className="page-narrow">
        <p className="error">Você não tem permissão para editar este torneio.</p>
        <p>
          <Link to={Number.isFinite(tid) ? `/torneios/${tid}` : "/torneios"}>Voltar</Link>
        </p>
      </div>
    );
  }

  return (
    <div className="page-narrow">
      <p>
        <Link to={`/torneios/${t.id}`}>← Voltar ao torneio</Link>
      </p>
      <h2 style={{ marginTop: 0 }}>Editar torneio</h2>
      <form className="card" onSubmit={onSubmit}>
        <div className="field">
          <label>Nome</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} />
        </div>
        <div className="field">
          <label>Número de vagas</label>
          <input
            type="number"
            min={Math.max(2, t.registrations_count)}
            max={512}
            value={maxParticipants}
            onChange={(e) => setMaxParticipants(Number(e.target.value))}
          />
          <small style={{ color: "var(--muted)", display: "block", marginTop: "0.25rem" }}>
            Inscritos atuais: {t.registrations_count} (mínimo permitido ao salvar)
          </small>
        </div>
        <div className="field">
          <label>Premiação</label>
          <textarea rows={3} value={prize} onChange={(e) => setPrize(e.target.value)} placeholder="Ex.: Troféu + R$ 500" />
        </div>
        <div className="field">
          <label>Valor da inscrição (R$)</label>
          <input
            type="number"
            min={0}
            step="0.01"
            value={Number.isFinite(registrationFee) ? registrationFee : 0}
            onChange={(e) => setRegistrationFee(parseFloat(e.target.value) || 0)}
          />
        </div>
        <div className="field">
          <label>Melhor de (sets por partida)</label>
          <select className="select" value={matchBestOf} onChange={(e) => setMatchBestOf(Number(e.target.value))}>
            <option value={1}>1 set</option>
            <option value={3}>3 sets</option>
            <option value={5}>5 sets</option>
            <option value={7}>7 sets</option>
          </select>
        </div>
        <div className="field">
          <label>Prazo de inscrição</label>
          <input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
          <small style={{ color: "var(--muted)", display: "block", marginTop: "0.25rem" }}>
            Deixe em branco para sem prazo definido.
          </small>
        </div>
        {err && <p className="error">{err}</p>}
        <div className="split-actions">
          <Link className="btn btn-ghost" to={`/torneios/${t.id}`}>
            Cancelar
          </Link>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </div>
      </form>
    </div>
  );
}
