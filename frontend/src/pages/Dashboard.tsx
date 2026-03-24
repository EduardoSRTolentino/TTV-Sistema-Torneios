import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Dashboard() {
  const { user } = useAuth();
  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Painel</h2>
      <p style={{ color: "var(--muted)" }}>
        Olá, <strong>{user?.full_name}</strong>. Papel: <span className="badge">{user?.role}</span>
      </p>
      <div className="grid-2" style={{ marginTop: "1rem" }}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Torneios</h3>
          <p style={{ color: "var(--muted)" }}>Veja torneios abertos e inscreva-se.</p>
          <Link to="/torneios" className="btn btn-primary">
            Ir para torneios
          </Link>
        </div>
        {(user?.role === "organizer" || user?.role === "admin") && (
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Organização</h3>
            <p style={{ color: "var(--muted)" }}>Crie um torneio e gerencie inscrições.</p>
            <Link to="/torneios/novo" className="btn btn-primary">
              Novo torneio
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
