import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();
  return (
    <div>
      <header
        style={{
          borderBottom: "1px solid var(--line)",
          background: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(8px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div className="container" style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "0.85rem 0" }}>
          <Link to="/" className="brand" style={{ fontWeight: 800, fontSize: "1.1rem" }}>
            TTV-TORNEIOS
          </Link>
          <nav style={{ display: "flex", gap: "1rem", flex: 1, flexWrap: "wrap" }}>
            <NavLink to="/torneios" style={({ isActive }) => ({ fontWeight: isActive ? 700 : 500 })}>
              Torneios
            </NavLink>
            <NavLink to="/ranking" style={({ isActive }) => ({ fontWeight: isActive ? 700 : 500 })}>
              Ranking
            </NavLink>
            {user && (
              <NavLink to="/painel" style={({ isActive }) => ({ fontWeight: isActive ? 700 : 500 })}>
                Painel
              </NavLink>
            )}
            {(user?.role === "organizer" || user?.role === "admin") && (
              <NavLink to="/torneios/novo" style={({ isActive }) => ({ fontWeight: isActive ? 700 : 500 })}>
                Novo torneio
              </NavLink>
            )}
          </nav>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {user ? (
              <>
                <span className="badge">{user.role}</span>
                <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{user.full_name}</span>
                <button className="btn btn-ghost" type="button" onClick={logout}>
                  Sair
                </button>
              </>
            ) : (
              <>
                <Link to="/entrar">Entrar</Link>
                <Link to="/cadastro" className="btn btn-primary" style={{ padding: "0.5rem 0.9rem" }}>
                  Cadastrar
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="container" style={{ padding: "1.5rem 0 3rem" }}>
        <Outlet />
      </main>
      <footer style={{ borderTop: "1px solid var(--line)", padding: "1.5rem 0", color: "var(--muted)", fontSize: "0.9rem" }}>
        <div className="container">TTV-Torneios — plataforma de torneios de tênis de mesa.</div>
      </footer>
    </div>
  );
}
