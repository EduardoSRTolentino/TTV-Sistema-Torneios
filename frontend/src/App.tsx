import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Protected } from "@/components/Protected";
import { Home } from "@/pages/Home";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Dashboard } from "@/pages/Dashboard";
import { TournamentList } from "@/pages/TournamentList";
import { TournamentDetail } from "@/pages/TournamentDetail";
import { CreateTournament } from "@/pages/CreateTournament";
import { OAuthCallback } from "@/pages/OAuthCallback";
import { Ranking } from "@/pages/Ranking";
import { useAuth } from "@/context/AuthContext";
import { AdminUsers } from "@/pages/AdminUsers";

function OrgOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Carregando…</p>;
  if (!user) return <Navigate to="/entrar" replace />;
  if (user.role !== "organizer" && user.role !== "admin") {
    return <p>Apenas organizadores ou administradores podem acessar esta página.</p>;
  }
  return <>{children}</>;
}

function AdminOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Carregando…</p>;
  if (!user) return <Navigate to="/entrar" replace />;
  if (user.role !== "admin") {
    return <p>Apenas administradores podem acessar esta página.</p>;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/entrar" element={<Login />} />
        <Route path="/cadastro" element={<Register />} />
        <Route path="/oauth-callback" element={<OAuthCallback />} />
        <Route
          path="/ranking"
          element={
            <Protected>
              <Ranking />
            </Protected>
          }
        />
        <Route
          path="/torneios"
          element={
            <Protected>
              <TournamentList />
            </Protected>
          }
        />
        <Route
          path="/torneios/novo"
          element={
            <Protected>
              <OrgOnly>
                <CreateTournament />
              </OrgOnly>
            </Protected>
          }
        />
        <Route
          path="/torneios/:id"
          element={
            <Protected>
              <TournamentDetail />
            </Protected>
          }
        />
        <Route
          path="/painel"
          element={
            <Protected>
              <Dashboard />
            </Protected>
          }
        />
        <Route
          path="/admin/usuarios"
          element={
            <Protected>
              <AdminOnly>
                <AdminUsers />
              </AdminOnly>
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
