import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Carregando…</p>;
  if (!user) return <Navigate to="/entrar" replace />;
  return <>{children}</>;
}
