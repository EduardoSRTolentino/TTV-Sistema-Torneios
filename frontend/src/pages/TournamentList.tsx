import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/api/client";
import type { Tournament } from "@/api/types";

function statusLabel(s: Tournament["status"]) {
  const map: Record<Tournament["status"], string> = {
    draft: "Rascunho",
    registration_open: "Inscrições abertas",
    registration_closed: "Inscrições fechadas",
    in_progress: "Em andamento",
    completed: "Concluído",
  };
  return map[s];
}

export function TournamentList() {
  const [items, setItems] = useState<Tournament[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .listTournaments()
      .then(setItems)
      .catch(() => setErr("Não foi possível carregar os torneios."));
  }, []);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Torneios</h2>
      {err && <p className="error">{err}</p>}
      <div style={{ display: "grid", gap: "1rem" }}>
        {items.map((t) => (
          <Link key={t.id} to={`/torneios/${t.id}`} className="card" style={{ display: "block", color: "inherit" }}>
            <div className="tournament-row">
              <div>
                <strong style={{ fontSize: "1.1rem" }}>{t.title}</strong>
                <div style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: "0.25rem" }}>
                  {t.game_format === "singles" ? "Individual" : "Duplas"} • {t.registrations_count} inscritos
                </div>
              </div>
              <span className="badge">{statusLabel(t.status)}</span>
            </div>
          </Link>
        ))}
        {!items.length && !err && <p style={{ color: "var(--muted)" }}>Nenhum torneio cadastrado ainda.</p>}
      </div>
    </div>
  );
}
