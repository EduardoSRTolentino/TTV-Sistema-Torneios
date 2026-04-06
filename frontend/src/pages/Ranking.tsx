import { useEffect, useState } from "react";
import * as api from "@/api/client";

type Row = {
  user_id: number;
  full_name: string;
  rating: number;
  ranking_points?: number;
  combined_score?: number;
  games_played: number;
};

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
      <h2 style={{ marginTop: 0 }}>Ranking global</h2>
      <p style={{ color: "var(--muted)" }}>
        Ordenação por ELO + pontos de torneios (premiação configurada nos torneios). Coluna &quot;Total&quot; soma os dois.
      </p>
      {err && <p className="error">{err}</p>}
      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Jogador</th>
                <th>ELO</th>
                <th>Pts torneios</th>
                <th>Total</th>
                <th>Partidas</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.user_id}>
                  <td>{i + 1}</td>
                  <td>{r.full_name}</td>
                  <td>{r.rating.toFixed(1)}</td>
                  <td>{(r.ranking_points ?? 0).toFixed(1)}</td>
                  <td>{(r.combined_score ?? r.rating + (r.ranking_points ?? 0)).toFixed(1)}</td>
                  <td>{r.games_played}</td>
                </tr>
              ))}
              {!rows.length && !err && (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)", padding: "0.75rem 0" }}>
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
