import { Link } from "react-router-dom";

export function Home() {
  return (
    <div className="grid-2" style={{ alignItems: "center" }}>
      <div>
        <p className="badge" style={{ marginBottom: "0.75rem" }}>
          Tênis de mesa • Torneios
        </p>
        <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", margin: "0 0 0.75rem" }}>Inscrições e chaves no ritmo eSports</h1>
        <p style={{ color: "var(--muted)", lineHeight: 1.6, marginBottom: "1.25rem" }}>
          Gerencie torneios individuais ou em dupla, abra inscrições com limite de vagas e gere mata-mata automaticamente.
        </p>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Link to="/torneios" className="btn btn-primary">
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
