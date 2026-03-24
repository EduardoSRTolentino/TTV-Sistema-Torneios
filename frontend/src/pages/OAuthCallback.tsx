import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import * as api from "@/api/client";
import { useAuth } from "@/context/AuthContext";

const API_ORIGIN = import.meta.env.VITE_API_ORIGIN ?? "";

export function OAuthCallback() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setErr("Token ausente na URL.");
      return;
    }
    api.setAuthToken(token);
    refresh()
      .then(() => nav("/painel"))
      .catch(() => setErr("Não foi possível validar a sessão."));
  }, [params, nav, refresh]);

  return (
    <div className="card" style={{ maxWidth: 420, margin: "2rem auto" }}>
      <h2 style={{ marginTop: 0 }}>Login OAuth</h2>
      {err ? <p className="error">{err}</p> : <p>Finalizando login…</p>}
      {!API_ORIGIN && (
        <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          Defina VITE_API_ORIGIN no .env para o link &quot;Entrar com Google&quot; apontar para o backend.
        </p>
      )}
    </div>
  );
}
