import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { User } from "@/api/types";
import * as api from "@/api/client";

type AuthState = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = localStorage.getItem("ttv_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      api.setAuthToken(token);
      const u = await api.me();
      setUser(u);
    } catch {
      api.setAuthToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const logout = useCallback(() => {
    api.setAuthToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, refresh, logout }), [user, loading, refresh, logout]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth fora do provider");
  return v;
}
