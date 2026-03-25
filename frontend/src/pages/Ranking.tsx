import { useEffect, useState } from "react";
import * as api from "@/api/client";

type Row = { user_id: number; full_name: string; rating: number; games_played: number };

export function Ranking() {
  const [rows, setRows] = useState<Row[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .listRanking()
      .then(setRows)
      .catch(() => setErr("Não foi possível carregar o ranking."));
  }, []);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Ranking global (ELO)</h2>
      <p style={{ color: "var(--muted)" }}>Atualizado conforme resultados registrados (Fase 2).</p>
      {err && <p className="error">{err}</p>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Jogador</th>
                <th>ELO</th>
                <th>Partidas</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.user_id}>
                  <td>{i + 1}</td>
                  <td>{r.full_name}</td>
                  <td>{r.rating.toFixed(1)}</td>
                  <td>{r.games_played}</td>
                </tr>
              ))}
              {!rows.length && !err && (
                <tr>
                  <td colSpan={4} style={{ color: "var(--muted)", padding: "0.75rem 0" }}>
                    Nenhum dado ainda — o ranking preenche após partidas oficiais.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
