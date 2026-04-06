import type { BracketMatch } from "@/api/types";

type Props = {
  rounds: [number, BracketMatch[]][];
  canDeclareResults: boolean;
  busyMatchId: number | null;
  onDeclareWinner: (matchId: number, winnerRegId: number) => void;
  onOpenSetForm?: (match: BracketMatch) => void;
};

export function BracketTree({
  rounds,
  canDeclareResults,
  busyMatchId,
  onDeclareWinner,
  onOpenSetForm,
}: Props) {
  if (!rounds.length) return null;

  return (
    <div className="bracket-view">
      {rounds.map(([roundNum, items]) => {
        const phase = items[0]?.round_label || `Rodada ${roundNum}`;
        return (
          <div key={roundNum} className="bracket-column">
            <h4 className="bracket-phase-title">{phase}</h4>
            <ul className="bracket-match-list">
              {items.map((m) => {
                const status = m.status ?? "pending";
                const pendingResult =
                  canDeclareResults &&
                  m.reg1_id != null &&
                  m.reg2_id != null &&
                  m.winner_reg_id == null &&
                  status !== "finished";
                return (
                  <li key={m.id} className="bracket-match-card">
                    <p className="bracket-card-phase-label">{m.round_label}</p>
                    <div className="bracket-slot">
                      <span className={m.winner_reg_id === m.reg1_id ? "bracket-winner" : ""}>{m.reg1_display}</span>
                    </div>
                    <div className="bracket-vs">vs</div>
                    <div className="bracket-slot">
                      <span className={m.winner_reg_id === m.reg2_id ? "bracket-winner" : ""}>{m.reg2_display}</span>
                    </div>
                    {m.sets && m.sets.length > 0 ? (
                      <ul className="bracket-set-history">
                        {m.sets.map((s) => (
                          <li key={s.set_number}>
                            Set {s.set_number}: {s.reg1_score} × {s.reg2_score}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {m.winner_reg_id != null && (
                      <p className="bracket-winner-line">
                        Vencedor: <strong>{m.winner_display ?? "—"}</strong>
                      </p>
                    )}
                    {pendingResult && (
                      <div className="bracket-actions bracket-actions--stack">
                        {onOpenSetForm ? (
                          <button
                            type="button"
                            className="btn btn-primary bracket-win-btn"
                            disabled={busyMatchId === m.id}
                            onClick={() => onOpenSetForm(m)}
                          >
                            {busyMatchId === m.id ? "…" : "Registrar sets"}
                          </button>
                        ) : null}
                        <div className="bracket-actions">
                          <button
                            type="button"
                            className="btn btn-ghost bracket-win-btn"
                            disabled={busyMatchId === m.id}
                            onClick={() => onDeclareWinner(m.id, m.reg1_id!)}
                          >
                            {busyMatchId === m.id ? "…" : `Vitória rápida: ${m.reg1_display}`}
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost bracket-win-btn"
                            disabled={busyMatchId === m.id}
                            onClick={() => onDeclareWinner(m.id, m.reg2_id!)}
                          >
                            {busyMatchId === m.id ? "…" : `Vitória rápida: ${m.reg2_display}`}
                          </button>
                        </div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
