import { useEffect, useState } from "react";
import * as api from "@/api/client";

export function AdminSettings() {
  const [initialRanking, setInitialRanking] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const s = await api.getSystemSettings();
        if (!cancelled) {
          setInitialRanking(String(s.initial_ranking));
        }
      } catch {
        if (!cancelled) setErr("Não foi possível carregar as configurações.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    const n = Number(initialRanking);
    if (!Number.isFinite(n) || n < 0 || !Number.isInteger(n)) {
      setErr("Informe um número inteiro maior ou igual a zero.");
      return;
    }
    setSaving(true);
    try {
      const s = await api.patchSystemSettings({ initial_ranking: n });
      setInitialRanking(String(s.initial_ranking));
      setMsg("Configurações salvas. Novos jogadores usarão este ranking inicial.");
    } catch {
      setErr("Não foi possível salvar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Configurações do sistema</h2>
      <p style={{ color: "var(--muted)" }}>
        O ranking inicial (ELO) é aplicado a novos cadastros (e-mail/senha, Google OAuth e usuários criados pelo admin).
        Usuários já existentes não são alterados automaticamente.
      </p>

      {loading ? (
        <p>Carregando…</p>
      ) : (
        <form className="card" style={{ marginTop: "1rem", maxWidth: "28rem" }} onSubmit={onSave}>
          <div className="field">
            <label htmlFor="initial-ranking">Ranking inicial (ELO)</label>
            <input
              id="initial-ranking"
              type="number"
              min={0}
              step={1}
              value={initialRanking}
              onChange={(e) => setInitialRanking(e.target.value)}
              required
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}

      {msg && <p className="success" style={{ marginTop: "1rem" }}>{msg}</p>}
      {err && <p className="error" style={{ marginTop: "1rem" }}>{err}</p>}
    </div>
  );
}
