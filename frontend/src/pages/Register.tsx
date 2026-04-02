import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as api from "@/api/client";
import { PasswordField } from "@/components/PasswordField";
import { useAuth } from "@/context/AuthContext";
import { PASSWORD_HINT, passwordValidationError } from "@/lib/passwordRules";
import axios from "axios";

function registerErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const d = err.response?.data as { detail?: unknown } | undefined;
    const detail = d?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === "object" && detail[0] !== null) {
      const msg = (detail[0] as { msg?: string }).msg;
      if (msg) return msg;
    }
  }
  return "Não foi possível cadastrar. Verifique os dados ou se o e-mail já existe.";
}

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
    const pwdErr = passwordValidationError(password);
    if (pwdErr) {
      setErr(pwdErr);
      return;
    }
    try {
      await api.register({ email, password, full_name });
      await api.login(email, password);
      await refresh();
      nav("/painel");
    } catch (err) {
      setErr(registerErrorMessage(err));
    }
  }

  return (
    <div className="page-auth">
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
          <label htmlFor="register-password">Senha</label>
          <PasswordField
            id="register-password"
            value={password}
            onChange={setPassword}
            required
            autoComplete="new-password"
          />
          <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--muted)", lineHeight: 1.4 }}>
            {PASSWORD_HINT}
          </p>
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
