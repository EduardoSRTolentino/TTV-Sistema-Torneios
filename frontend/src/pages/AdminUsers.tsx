import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import * as api from "@/api/client";
import type { User, UserRole } from "@/api/types";
import { useAuth } from "@/context/AuthContext";

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function roleLabel(r: UserRole) {
  switch (r) {
    case "admin":
      return "Administrador";
    case "organizer":
      return "Organizador";
    case "player":
      return "Jogador";
  }
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

export function AdminUsers() {
  const { user: currentUser } = useAuth();
  const [rows, setRows] = useState<User[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [rankDraft, setRankDraft] = useState<Record<number, string>>({});
  const [rankSavingId, setRankSavingId] = useState<number | null>(null);
  const [roleDraft, setRoleDraft] = useState<Partial<Record<number, UserRole>>>({});
  const [roleSavingId, setRoleSavingId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const data = await api.listUsers();
      setRows(data);
      setRoleDraft({});
    } catch {
      setErr("Não foi possível carregar usuários.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load().catch(() => null);
  }, []);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return rows;
    return rows.filter((u) => (u.full_name + " " + u.email).toLowerCase().includes(term));
  }, [rows, q]);

  function effectiveRole(u: User): UserRole {
    return roleDraft[u.id] ?? u.role;
  }

  async function onSaveRole(u: User) {
    if (currentUser && u.id === currentUser.id) return;
    const next = effectiveRole(u);
    if (next === u.role) return;
    setErr(null);
    setMsg(null);
    setRoleSavingId(u.id);
    try {
      const updated = await api.setUserRole(u.id, next);
      setRows((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
      setRoleDraft((d) => {
        const nextDraft = { ...d };
        delete nextDraft[u.id];
        return nextDraft;
      });
      setMsg(`Cargo de ${updated.full_name} atualizado para ${roleLabel(updated.role)}.`);
    } catch (e) {
      setErr(apiDetailMessage(e) ?? "Não foi possível atualizar o cargo.");
    } finally {
      setRoleSavingId(null);
    }
  }

  function rankInputValue(u: User) {
    if (rankDraft[u.id] !== undefined) return rankDraft[u.id]!;
    if (u.rating != null && Number.isFinite(u.rating)) return String(u.rating);
    return "";
  }

  async function onSaveRanking(u: User) {
    setErr(null);
    setMsg(null);
    const raw = rankInputValue(u).trim();
    const n = Number(raw);
    if (!Number.isFinite(n) || n < 0) {
      setErr("Ranking inválido: informe um número ≥ 0.");
      return;
    }
    setRankSavingId(u.id);
    try {
      const updated = await api.patchUserRanking(u.id, n);
      setRows((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
      setRankDraft((d) => {
        const next = { ...d };
        delete next[u.id];
        return next;
      });
      setMsg(`Ranking de ${updated.full_name} atualizado.`);
    } catch {
      setErr("Não foi possível atualizar o ranking.");
    } finally {
      setRankSavingId(null);
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Administração • Usuários</h2>
      <p style={{ color: "var(--muted)" }}>
        Apenas administradores alteram cargos. Promova jogadores a <strong>organizador</strong> para que criem torneios. Você
        não pode alterar o próprio cargo.
      </p>

      <div className="card" style={{ marginTop: "1rem" }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Buscar</label>
          <input
            placeholder="Nome ou e-mail…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            autoComplete="off"
          />
        </div>
      </div>

      {msg && <p className="success">{msg}</p>}
      {err && <p className="error">{err}</p>}

      <div className="card" style={{ marginTop: "1rem" }}>
        <h3 style={{ marginTop: 0 }}>Lista</h3>
        {loading ? (
          <p>Carregando…</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left" }}>
                  <th style={{ padding: "0.5rem 0.25rem" }}>ID</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>Nome</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>E-mail</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>Ranking (ELO)</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>Cargo atual</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>Criado em</th>
                  <th style={{ padding: "0.5rem 0.25rem" }}>Alterar cargo</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id} style={{ borderTop: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.5rem 0.25rem", color: "var(--muted)" }}>#{u.id}</td>
                    <td style={{ padding: "0.5rem 0.25rem" }}>{u.full_name}</td>
                    <td style={{ padding: "0.5rem 0.25rem", color: "var(--muted)" }}>{u.email}</td>
                    <td style={{ padding: "0.5rem 0.25rem", minWidth: "11rem" }}>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                        <input
                          type="number"
                          min={0}
                          step="any"
                          value={rankInputValue(u)}
                          onChange={(e) =>
                            setRankDraft((d) => ({
                              ...d,
                              [u.id]: e.target.value,
                            }))
                          }
                          style={{ width: "6.5rem" }}
                          aria-label={`Ranking ELO de ${u.full_name}`}
                        />
                        <button
                          type="button"
                          className="btn btn-ghost"
                          style={{ padding: "0.35rem 0.5rem", fontSize: "0.85rem" }}
                          disabled={rankSavingId === u.id}
                          onClick={() => onSaveRanking(u)}
                        >
                          {rankSavingId === u.id ? "…" : "Salvar"}
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: "0.5rem 0.25rem" }}>
                      <span className="badge">{roleLabel(u.role)}</span>
                    </td>
                    <td style={{ padding: "0.5rem 0.25rem", color: "var(--muted)" }}>{formatDate(u.created_at)}</td>
                    <td style={{ padding: "0.5rem 0.25rem" }}>
                      {currentUser && u.id === currentUser.id ? (
                        <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                          Não é possível alterar seu próprio cargo.
                        </span>
                      ) : (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                          <select
                            value={effectiveRole(u)}
                            onChange={(e) =>
                              setRoleDraft((d) => ({
                                ...d,
                                [u.id]: e.target.value as UserRole,
                              }))
                            }
                            className="select"
                            aria-label={`Novo cargo de ${u.email}`}
                          >
                            <option value="player">Jogador</option>
                            <option value="organizer">Organizador</option>
                            <option value="admin">Administrador</option>
                          </select>
                          <button
                            type="button"
                            className="btn btn-ghost"
                            style={{ padding: "0.35rem 0.5rem", fontSize: "0.85rem" }}
                            disabled={roleSavingId === u.id || effectiveRole(u) === u.role}
                            onClick={() => onSaveRole(u)}
                          >
                            {roleSavingId === u.id ? "…" : "Salvar cargo"}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {!filtered.length && (
                  <tr>
                    <td colSpan={7} style={{ padding: "0.75rem 0.25rem", color: "var(--muted)" }}>
                      Nenhum usuário encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

