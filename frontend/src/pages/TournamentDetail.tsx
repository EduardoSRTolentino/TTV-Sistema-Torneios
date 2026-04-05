import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "@/api/client";
import type { BracketMatch, Registration, Tournament } from "@/api/types";
import { useAuth } from "@/context/AuthContext";

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

  const canManage =
    user &&
    t &&
    (user.role === "admin" || (user.role === "organizer" && t.organizer_id === user.id));

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
    try {
      await api.closeRegistration(tid);
      await load();
    } catch {
      setErr("Não foi possível fechar inscrições.");
    }
  }

  async function onGenerate() {
    setErr(null);
    try {
      await api.generateBracket(tid);
      setMsg("Chaveamento gerado.");
      await load();
    } catch {
      setErr("Não foi possível gerar o chaveamento (mínimo 2 inscrições e status adequado).");
    }
  }

  const rounds = useMemo(() => {
    const m = new Map<number, BracketMatch[]>();
    bracket.forEach((b) => {
      const arr = m.get(b.round_number) ?? [];
      arr.push(b);
      m.set(b.round_number, arr);
    });
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
        <span className="badge">{t.status}</span>
        <span>
          {t.game_format === "singles" ? "Individual" : "Duplas"} • {t.registrations_count}/{t.max_participants}{" "}
          inscritos
          {(t.registration_fee ?? 0) > 0 ? ` • Inscrição: R$ ${(t.registration_fee ?? 0).toFixed(2)}` : ""}
        </span>
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
          <div className="split-actions">
            <Link className="btn btn-ghost" to={`/torneios/${t.id}/editar`}>
              Editar torneio
            </Link>
            {t.status === "registration_open" && (
              <button className="btn btn-ghost" type="button" onClick={onClose}>
                Fechar inscrições
              </button>
            )}
            <button className="btn btn-primary" type="button" onClick={onGenerate}>
              Gerar chaveamento (mata-mata)
            </button>
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
            </li>
          ))}
          {!regs.length && <li style={{ color: "var(--muted)" }}>Nenhuma inscrição ainda.</li>}
        </ul>
      </div>

      {!!rounds.length && (
        <div style={{ marginTop: "1rem" }}>
          <h3>Chaveamento</h3>
          {rounds.map(([round, items]) => (
            <div key={round} className="card" style={{ marginBottom: "0.75rem" }}>
              <strong>Rodada {round}</strong>
              <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.1rem" }}>
                {items.map((m) => (
                  <li key={m.id}>
                    Partida {m.position_in_round + 1}: {m.reg1_id ?? "bye"} vs {m.reg2_id ?? "bye"}
                    {m.winner_reg_id ? ` → vencedor reg ${m.winner_reg_id}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
