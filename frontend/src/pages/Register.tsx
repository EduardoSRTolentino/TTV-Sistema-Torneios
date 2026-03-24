import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as api from "@/api/client";
import { useAuth } from "@/context/AuthContext";

export function Register() {
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [full_name, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api.register({ email, password, full_name });
      await api.login(email, password);
      await refresh();
      nav("/painel");
    } catch {
      setErr("Não foi possível cadastrar. Verifique os dados ou se o e-mail já existe.");
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>Cadastro</h2>
      <form className="card" onSubmit={onSubmit}>
        <div className="field">
          <label>Nome completo</label>
          <input value={full_name} onChange={(e) => setFullName(e.target.value)} required minLength={2} />
        </div>
        <div className="field">
          <label>E-mail</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label>Senha (mín. 6)</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        </div>
        {err && <p className="error">{err}</p>}
        <button className="btn btn-primary" type="submit" style={{ width: "100%" }}>
          Criar conta
        </button>
        <p style={{ marginTop: "1rem", color: "var(--muted)" }}>
          Já tem conta? <Link to="/entrar">Entrar</Link>
        </p>
      </form>
    </div>
  );
}
