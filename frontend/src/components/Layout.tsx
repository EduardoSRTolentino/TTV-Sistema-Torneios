import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : undefined);

  return (
    <div>
      <header className={`site-header${menuOpen ? " menu-open" : ""}`}>
        <div className="container header-row">
          <Link to="/" className="header-brand">
            TTV-TORNEIOS
          </Link>
          <div className="header-spacer" aria-hidden />
          <nav
            id="navegacao-principal"
            className={`site-nav${menuOpen ? " is-open" : ""}`}
            aria-label="Navegação principal"
          >
            {user && (
              <NavLink to="/torneios" className={navClass} end>
                Torneios
              </NavLink>
            )}
            {user && (
              <NavLink to="/ranking" className={navClass}>
                Ranking
              </NavLink>
            )}
            {user && (
              <NavLink to="/painel" className={navClass}>
                Painel
              </NavLink>
            )}
            {user?.role === "admin" && (
              <NavLink to="/admin/usuarios" className={navClass}>
                Usuários
              </NavLink>
            )}
            {user?.role === "admin" && (
              <NavLink to="/admin/configuracoes" className={navClass}>
                Configurações
              </NavLink>
            )}
            {(user?.role === "organizer" || user?.role === "admin") && (
              <NavLink to="/torneios/novo" className={navClass}>
                Novo torneio
              </NavLink>
            )}
            <div className="site-nav__mobile-auth">
              {user ? (
                <>
                  <span className="badge">{user.role}</span>
                  <span style={{ color: "var(--muted)" }}>{user.full_name}</span>
                  <button className="btn btn-ghost" type="button" onClick={() => { logout(); setMenuOpen(false); }}>
                    Sair
                  </button>
                </>
              ) : (
                <>
                  <Link to="/entrar" className="btn btn-ghost" onClick={() => setMenuOpen(false)}>
                    Entrar
                  </Link>
                  <Link to="/cadastro" className="btn btn-primary" onClick={() => setMenuOpen(false)}>
                    Cadastrar
                  </Link>
                </>
              )}
            </div>
          </nav>
          <div className="header-auth-desktop">
            {user ? (
              <>
                <span className="badge">{user.role}</span>
                <span className="header-user-name" title={user.full_name}>
                  {user.full_name}
                </span>
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
          <button
            type="button"
            className={`menu-toggle${menuOpen ? " is-active" : ""}`}
            aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={menuOpen}
            aria-controls="navegacao-principal"
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span className="menu-toggle-inner" aria-hidden>
              <span className="menu-toggle-bar" />
              <span className="menu-toggle-bar" />
              <span className="menu-toggle-bar" />
            </span>
          </button>
        </div>
        <button
          type="button"
          className={`nav-backdrop${menuOpen ? " is-open" : ""}`}
          aria-label="Fechar menu"
          tabIndex={-1}
          onClick={() => setMenuOpen(false)}
        />
      </header>
      <main id="conteudo-principal" className="container site-main">
        <Outlet />
      </main>
      <footer className="site-footer">
        <div className="container">TTV-Torneios — plataforma de torneios de tênis de mesa.</div>
      </footer>
    </div>
  );
}
