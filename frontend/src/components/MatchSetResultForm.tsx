import { FormEvent, useMemo, useState } from "react";
import type { BracketMatch, Tournament } from "@/api/types";
import { validateMatchSets, type SetInputRow } from "@/lib/matchValidation";

type Props = {
  tournament: Tournament;
  match: BracketMatch;
  busy: boolean;
  onSubmit: (sets: SetInputRow[]) => Promise<void>;
  onCancel: () => void;
};

function emptyRows(count: number): SetInputRow[] {
  return Array.from({ length: count }, (_, i) => ({
    set_number: i + 1,
    reg1_score: 0,
    reg2_score: 0,
  }));
}

export function MatchSetResultForm({ tournament, match, busy, onSubmit, onCancel }: Props) {
  const initialCount = Math.min(
    tournament.match_best_of_sets,
    Math.max(Math.floor((tournament.match_best_of_sets + 1) / 2), 1),
  );
  const [rows, setRows] = useState<SetInputRow[]>(() => emptyRows(initialCount));
  const [localErr, setLocalErr] = useState<string | null>(null);

  const pointsPerSet = tournament.match_points_per_set ?? 11;
  const bestOf = tournament.match_best_of_sets ?? 3;

  const preview = useMemo(
    () => validateMatchSets(match.reg1_id!, match.reg2_id!, rows, bestOf, pointsPerSet),
    [match.reg1_id, match.reg2_id, rows, bestOf, pointsPerSet],
  );

  function updateRow(i: number, field: "reg1_score" | "reg2_score", raw: string) {
    const n = parseInt(raw, 10);
    setRows((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], [field]: Number.isFinite(n) ? n : 0 };
      return next;
    });
  }

  function addSet() {
    if (rows.length >= bestOf) return;
    setRows((prev) => [...prev, { set_number: prev.length + 1, reg1_score: 0, reg2_score: 0 }]);
  }

  function removeLastSet() {
    if (rows.length <= 1) return;
    setRows((prev) => prev.slice(0, -1).map((r, i) => ({ ...r, set_number: i + 1 })));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLocalErr(null);
    const v = validateMatchSets(match.reg1_id!, match.reg2_id!, rows, bestOf, pointsPerSet);
    if (!v.ok) {
      setLocalErr(v.message);
      return;
    }
    await onSubmit(rows);
  }

  return (
    <form className="card match-set-form" onSubmit={handleSubmit}>
      <h4 style={{ marginTop: 0 }}>Placar por sets</h4>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: 0 }}>
        Melhor de {bestOf} sets • {pointsPerSet} pontos por set • vitória com diferença mínima de 2 (ex.: 11×9 válido, 11×10
        inválido).
      </p>
      <table className="data-table" style={{ width: "100%", marginTop: "0.75rem" }}>
        <thead>
          <tr>
            <th>Set</th>
            <th>{match.reg1_display ?? "Jogador 1"}</th>
            <th>{match.reg2_display ?? "Jogador 2"}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.set_number}>
              <td>{r.set_number}</td>
              <td>
                <input
                  type="number"
                  min={0}
                  className="input-narrow"
                  value={r.reg1_score}
                  onChange={(e) => updateRow(i, "reg1_score", e.target.value)}
                  aria-label={`Set ${r.set_number} placar ${match.reg1_display}`}
                />
              </td>
              <td>
                <input
                  type="number"
                  min={0}
                  className="input-narrow"
                  value={r.reg2_score}
                  onChange={(e) => updateRow(i, "reg2_score", e.target.value)}
                  aria-label={`Set ${r.set_number} placar ${match.reg2_display}`}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="split-actions" style={{ marginTop: "0.75rem" }}>
        <button type="button" className="btn btn-ghost" onClick={addSet} disabled={busy || rows.length >= bestOf}>
          + Set
        </button>
        <button type="button" className="btn btn-ghost" onClick={removeLastSet} disabled={busy || rows.length <= 1}>
          − Set
        </button>
      </div>
      {preview.ok ? (
        <p className="success" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
          Vencedor previsto:{" "}
          <strong>
            {preview.winnerRegId === match.reg1_id ? match.reg1_display : match.reg2_display}
          </strong>
        </p>
      ) : (
        <p className="error" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
          {preview.message}
        </p>
      )}
      {localErr && (
        <p className="error" style={{ marginTop: "0.5rem" }}>
          {localErr}
        </p>
      )}
      <div className="split-actions" style={{ marginTop: "1rem" }}>
        <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={busy}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-primary" disabled={busy || !preview.ok}>
          {busy ? "Salvando…" : "Finalizar partida"}
        </button>
      </div>
    </form>
  );
}
