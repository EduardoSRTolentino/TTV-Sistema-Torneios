import type { BracketMatch } from "@/api/types";

type Props = {
  rounds: [number, BracketMatch[]][];
  canDeclareResults: boolean;
  busyMatchId: number | null;
  onDeclareWinner: (matchId: number, winnerRegId: number) => void;
};

export function BracketTree({ rounds, canDeclareResults, busyMatchId, onDeclareWinner }: Props) {
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
                const pending =
                  canDeclareResults && m.reg1_id != null && m.reg2_id != null && m.winner_reg_id == null;
                return (
                  <li key={m.id} className="bracket-match-card">
                    <div className="bracket-slot">
                      <span className={m.winner_reg_id === m.reg1_id ? "bracket-winner" : ""}>{m.reg1_display}</span>
                    </div>
                    <div className="bracket-vs">vs</div>
                    <div className="bracket-slot">
                      <span className={m.winner_reg_id === m.reg2_id ? "bracket-winner" : ""}>{m.reg2_display}</span>
                    </div>
                    {m.winner_reg_id != null && (
                      <p className="bracket-winner-line">
                        Vencedor: <strong>{m.winner_display ?? "—"}</strong>
                      </p>
                    )}
                    {pending && (
                      <div className="bracket-actions">
                        <button
                          type="button"
                          className="btn btn-ghost bracket-win-btn"
                          disabled={busyMatchId === m.id}
                          onClick={() => onDeclareWinner(m.id, m.reg1_id!)}
                        >
                          {busyMatchId === m.id ? "…" : `Vitória: ${m.reg1_display}`}
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost bracket-win-btn"
                          disabled={busyMatchId === m.id}
                          onClick={() => onDeclareWinner(m.id, m.reg2_id!)}
                        >
                          {busyMatchId === m.id ? "…" : `Vitória: ${m.reg2_display}`}
                        </button>
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
