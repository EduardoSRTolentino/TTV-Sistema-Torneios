import { FormEvent, useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { Link, useParams } from "react-router-dom";
import * as api from "@/api/client";
import type { BracketMatch, Registration, Tournament } from "@/api/types";
import { BracketTree } from "@/components/BracketTree";
import { MatchSetResultForm } from "@/components/MatchSetResultForm";
import { useAuth } from "@/context/AuthContext";

function statusLabel(s: Tournament["status"]) {
  const map: Record<Tournament["status"], string> = {
    draft: "Rascunho",
    registration_open: "Inscrições abertas",
    registration_closed: "Inscrições encerradas",
    in_progress: "Em andamento",
    completed: "Finalizado",
  };
  return map[s];
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

export function TournamentDetail() {
  const { id } = useParams();
  const tid = Number(id);
  const { user } = useAuth();
  const [t, setT] = useState<Tournament | null>(null);
  const [regs, setRegs] = useState<Registration[]>([]);
  const [bracket, setBracket] = useState<BracketMatch[]>([]);
  const [partnerEmail, setPartnerEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<null | "close" | "start" | "bracket">(null);
  const [matchBusyId, setMatchBusyId] = useState<number | null>(null);
  const [setFormMatch, setSetFormMatch] = useState<BracketMatch | null>(null);

  const canManage =
    user &&
    t &&
    (user.role === "admin" || (user.role === "organizer" && t.organizer_id === user.id));

  const canStartTournament =
    canManage &&
    t &&
    t.status !== "draft" &&
    t.status !== "in_progress" &&
    t.status !== "completed";

  const canGenerateBracket = canManage && t && t.status === "registration_closed";

  const canDeclareResults = Boolean(canManage && t && t.status === "in_progress");

  async function load() {
    if (!id || Number.isNaN(tid)) return;
    const [tournament, registrations, b] = await Promise.all([
      api.getTournament(tid),
      api.listRegistrations(tid),
      api.getBracket(tid).catch(() => []),
    ]);
    setT(tournament);
    setRegs(registrations);
    setBracket(b);
  }

  useEffect(() => {
    load().catch(() => setErr("Erro ao carregar torneio."));
  }, [id, tid]);

  async function onRegister(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    try {
      await api.registerInTournament(tid, t?.game_format === "doubles" ? partnerEmail : undefined);
      setMsg("Inscrição realizada!");
      await load();
    } catch {
      setErr("Não foi possível inscrever. Verifique prazo, vagas ou se já está inscrito.");
    }
  }

  async function onClose() {
    setErr(null);
    setMsg(null);
    setBusy("close");
    try {
      await api.patchCloseRegistrations(tid);
      setMsg("Inscrições encerradas.");
      await load();
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível fechar inscrições.");
    } finally {
      setBusy(null);
    }
  }

  async function onStart() {
    setErr(null);
    setMsg(null);
    setBusy("start");
    try {
      await api.startTournament(tid);
      setMsg("Torneio iniciado (inscrições encerradas e chaveamento gerado, se necessário).");
      await load();
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível iniciar o torneio.");
    } finally {
      setBusy(null);
    }
  }

  async function onGenerate() {
    setErr(null);
    setMsg(null);
    setBusy("bracket");
    try {
      await api.generateBracket(tid);
      setMsg("Chaveamento gerado.");
      await load();
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível gerar o chaveamento (mínimo 2 inscrições e inscrições encerradas).");
    } finally {
      setBusy(null);
    }
  }

  async function onDeclareWinner(matchId: number, winnerRegId: number) {
    setErr(null);
    setMsg(null);
    setMatchBusyId(matchId);
    try {
      await api.setWinner(matchId, winnerRegId);
      setMsg("Resultado registrado.");
      await load();
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível registrar o vencedor.");
    } finally {
      setMatchBusyId(null);
    }
  }

  const rounds = useMemo(() => {
    const m = new Map<number, BracketMatch[]>();
    bracket.forEach((b) => {
      const arr = m.get(b.round_number) ?? [];
      arr.push(b);
      m.set(b.round_number, arr);
    });
    for (const arr of m.values()) {
      arr.sort((a, b) => {
        const oa = a.match_order ?? a.position_in_round + 1;
        const ob = b.match_order ?? b.position_in_round + 1;
        if (oa !== ob) return oa - ob;
        return a.position_in_round - b.position_in_round;
      });
    }
    return [...m.entries()].sort((a, b) => a[0] - b[0]);
  }, [bracket]);

  if (!t) return <p>Carregando…</p>;

  return (
    <div>
      <p>
        <Link to="/torneios">← Voltar</Link>
      </p>
      <h2 style={{ marginTop: 0 }}>{t.title}</h2>
      <p style={{ color: "var(--muted)" }}>{t.description || "Sem descrição."}</p>
      <p className="meta-inline" style={{ color: "var(--muted)" }}>
        <span className="badge">{statusLabel(t.status)}</span>
        <span>
          {t.game_format === "singles" ? "Individual" : "Duplas"} • {t.registrations_count}/{t.max_participants}{" "}
          inscritos
          {(t.registration_fee ?? 0) > 0 ? ` • Inscrição: R$ ${(t.registration_fee ?? 0).toFixed(2)}` : ""}
          {` • Melhor de ${t.match_best_of_sets ?? 3} sets (${t.match_points_per_set ?? 11} pts/set)`}
          {t.dispute_third_place ? " • Disputa de 3º lugar" : ""}
        </span>
      </p>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: "0.25rem" }}>
        Chaveamento competitivo por ranking (1º e 2º só na final); ordem de partidas na rodada segue a sequência de
        campanha; BYEs favorecem os melhores seeds. O ranking usado no seeding é congelado ao gerar o chaveamento.
      </p>
      {t.prize ? (
        <p style={{ marginTop: "0.5rem" }}>
          <strong>Premiação:</strong> {t.prize}
        </p>
      ) : null}

      {user && t.status === "registration_open" && (
        <form className="card" onSubmit={onRegister} style={{ marginTop: "1rem" }}>
          <h3 style={{ marginTop: 0 }}>Inscrição</h3>
          {t.game_format === "doubles" && (
            <div className="field">
              <label>E-mail do parceiro</label>
              <input type="email" value={partnerEmail} onChange={(e) => setPartnerEmail(e.target.value)} required />
            </div>
          )}
          <button className="btn btn-primary" type="submit">
            Inscrever-me
          </button>
        </form>
      )}

      {canManage && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3 style={{ marginTop: 0 }}>Organização</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: 0 }}>
            O prazo de inscrição, quando definido, encerra as inscrições automaticamente ao ser consultado o torneio.
            &quot;Iniciar torneio&quot; encerra inscrições se ainda estiverem abertas e gera o chaveamento.
          </p>
          <div className="split-actions">
            <Link className="btn btn-ghost" to={`/torneios/${t.id}/editar`}>
              Editar torneio
            </Link>
            {t.status === "registration_open" && (
              <button className="btn btn-ghost" type="button" disabled={busy !== null} onClick={onClose}>
                {busy === "close" ? "Encerrando…" : "Encerrar inscrições"}
              </button>
            )}
            {canStartTournament && (
              <button className="btn btn-primary" type="button" disabled={busy !== null} onClick={onStart}>
                {busy === "start" ? "Iniciando…" : "Iniciar torneio"}
              </button>
            )}
            {canGenerateBracket && (
              <button className="btn btn-ghost" type="button" disabled={busy !== null} onClick={onGenerate}>
                {busy === "bracket" ? "Gerando…" : "Gerar chaveamento (mata-mata)"}
              </button>
            )}
          </div>
        </div>
      )}

      {msg && <p className="success">{msg}</p>}
      {err && <p className="error">{err}</p>}

      <div className="card" style={{ marginTop: "1rem" }}>
        <h3 style={{ marginTop: 0 }}>Inscrições</h3>
        <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
          {regs.map((r) => (
            <li key={r.id}>
              #{r.id} — {r.user_full_name ?? `jogador ${r.user_id}`} (ranking{" "}
              {Number.isFinite(r.user_rating) ? Math.round(r.user_rating) : "—"})
              {r.partner_user_id
                ? ` + ${r.partner_full_name ?? `jogador ${r.partner_user_id}`} (ranking ${
                    Number.isFinite(r.partner_rating as number) ? Math.round(r.partner_rating as number) : "—"
                  })`
                : ""}
              {r.bracket_seed_rating != null && Number.isFinite(r.bracket_seed_rating)
                ? ` • seed (congelado): ${Math.round(r.bracket_seed_rating)}`
                : ""}
            </li>
          ))}
          {!regs.length && <li style={{ color: "var(--muted)" }}>Nenhuma inscrição ainda.</li>}
        </ul>
      </div>

      {!!rounds.length && (
        <div style={{ marginTop: "1rem" }}>
          <h3>Chaveamento</h3>
          <BracketTree
            rounds={rounds}
            canDeclareResults={canDeclareResults}
            busyMatchId={matchBusyId}
            onDeclareWinner={onDeclareWinner}
            onOpenSetForm={(m) => {
              setErr(null);
              setSetFormMatch(m);
            }}
          />
        </div>
      )}

      {setFormMatch && t && (
        <div style={{ marginTop: "1rem" }}>
          <MatchSetResultForm
            tournament={t}
            match={setFormMatch}
            busy={matchBusyId === setFormMatch.id}
            onCancel={() => setSetFormMatch(null)}
            onSubmit={async (sets) => {
              setErr(null);
              setMsg(null);
              setMatchBusyId(setFormMatch.id);
              try {
                await api.submitMatchResult(setFormMatch.id, sets);
                setSetFormMatch(null);
                setMsg("Placar registrado.");
                await load();
              } catch (e) {
                setErr(apiDetailMessage(e) ?? "Não foi possível salvar o placar.");
              } finally {
                setMatchBusyId(null);
              }
            }}
          />
        </div>
      )}
    </div>
  );
}
