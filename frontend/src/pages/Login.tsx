import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as api from "@/api/client";
import { useAuth } from "@/context/AuthContext";

const API_ORIGIN = import.meta.env.VITE_API_ORIGIN ?? "";

export function Login() {
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api.login(email, password);
      await refresh();
      nav("/painel");
    } catch {
      setErr("E-mail ou senha inválidos.");
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>Entrar</h2>
      <form className="card" onSubmit={onSubmit}>
        <div className="field">
          <label>E-mail</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </div>
        <div className="field">
          <label>Senha</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        {err && <p className="error">{err}</p>}
        <button className="btn btn-primary" type="submit" style={{ width: "100%" }}>
          Entrar
        </button>
        {API_ORIGIN && (
          <p style={{ marginTop: "1rem" }}>
            <a className="btn btn-ghost" style={{ width: "100%", display: "block", textAlign: "center" }} href={`${API_ORIGIN}/auth/google/start`}>
              Entrar com Google
            </a>
          </p>
        )}
        <p style={{ marginTop: "1rem", color: "var(--muted)" }}>
          Não tem conta? <Link to="/cadastro">Cadastre-se</Link>
        </p>
      </form>
    </div>
  );
}
