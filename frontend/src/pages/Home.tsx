import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Home() {
  const { user } = useAuth();
  const torneiosTo = user ? "/torneios" : "/entrar";

  return (
    <div className="grid-2">
      <div>
        <p className="badge" style={{ marginBottom: "0.75rem" }}>
          Tênis de mesa • Torneios
        </p>
        <h1>Inscrições e chaves no ritmo eSports</h1>
        <p style={{ color: "var(--muted)", lineHeight: 1.6, marginBottom: "1.25rem" }}>
          Gerencie torneios individuais ou em dupla, abra inscrições com limite de vagas e gere mata-mata automaticamente.
        </p>
        <div className="hero-ctas">
          <Link to={torneiosTo} className="btn btn-primary">
            Ver torneios
          </Link>
          <Link to="/cadastro" className="btn btn-ghost">
            Criar conta
          </Link>
        </div>
      </div>
      <div className="card" style={{ background: "linear-gradient(145deg,#fff,#fff7ed)" }}>
        <h3 style={{ marginTop: 0 }}>Fluxo rápido</h3>
        <ol style={{ margin: 0, paddingLeft: "1.1rem", color: "var(--muted)", lineHeight: 1.7 }}>
          <li>Organizador cria o torneio e abre inscrições</li>
          <li>Jogadores se inscrevem (sem aprovação manual)</li>
          <li>Fechamento e geração automática do chaveamento</li>
        </ol>
      </div>
    </div>
  );
}
