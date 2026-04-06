import type { GroupDetail, GroupMatchRow, Tournament } from "@/api/types";
import { MatchSetResultForm } from "@/components/MatchSetResultForm";
import type { BracketMatch } from "@/api/types";

type Props = {
  tournament: Tournament;
  groups: GroupDetail[];
  canManage: boolean;
  busyMatchId: number | null;
  openGroupMatch: GroupMatchRow | null;
  onOpenSetForm: (m: GroupMatchRow) => void;
  onCloseSetForm: () => void;
  onSubmitSets: (
    match: GroupMatchRow,
    sets: Array<{ set_number: number; reg1_score: number; reg2_score: number }>,
  ) => Promise<void>;
};

function toBracketMatch(m: GroupMatchRow, tid: number): BracketMatch {
  return {
    id: m.id,
    tournament_id: tid,
    round_number: 0,
    position_in_round: 0,
    reg1_id: m.reg1_id,
    reg2_id: m.reg2_id,
    winner_reg_id: m.winner_reg_id,
    next_match_id: null,
    status: m.status === "pending" ? "pending" : "finished",
  };
}

export function GroupPhaseSection({
  tournament,
  groups,
  canManage,
  busyMatchId,
  openGroupMatch,
  onOpenSetForm,
  onCloseSetForm,
  onSubmitSets,
}: Props) {
  if (!groups.length) {
    return <p style={{ color: "var(--muted)" }}>Nenhum grupo gerado ainda.</p>;
  }

  return (
    <div className="group-phase">
      {groups.map((g) => (
        <div key={g.id} className="card" style={{ marginTop: "1rem" }}>
          <h4 style={{ marginTop: 0 }}>Grupo {g.name}</h4>
          <div className="table-wrap" style={{ overflowX: "auto" }}>
            <table className="standings-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Jogador</th>
                  <th>Pts</th>
                  <th>V</th>
                  <th>D</th>
                  <th>Sets</th>
                  <th>Saldo pts</th>
                </tr>
              </thead>
              <tbody>
                {g.standings.map((s) => (
                  <tr key={s.registration_id}>
                    <td>{s.rank_position || "—"}</td>
                    <td>{s.display_name}</td>
                    <td>{s.points}</td>
                    <td>{s.wins}</td>
                    <td>{s.losses}</td>
                    <td>
                      {s.sets_won}-{s.sets_lost}
                    </td>
                    <td>{s.points_scored - s.points_conceded}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h5 style={{ marginBottom: "0.5rem" }}>Partidas</h5>
          <ul className="group-match-list" style={{ margin: 0, paddingLeft: 0, listStyle: "none" }}>
            {g.matches
              .slice()
              .sort((a, b) => a.match_order - b.match_order)
              .map((m) => {
                const pending =
                  canManage &&
                  tournament.status === "in_progress" &&
                  m.status === "pending" &&
                  m.reg1_id != null &&
                  m.reg2_id != null;
                return (
                  <li key={m.id} className="group-match-row">
                    <span className="group-match-players">
                      {m.reg1_display} <strong>vs</strong> {m.reg2_display}
                    </span>
                    {m.winner_display && (
                      <span className="group-match-winner" style={{ marginLeft: "0.5rem", color: "var(--muted)" }}>
                        Vencedor: {m.winner_display}
                        {m.status === "walkover" ? " (WO)" : ""}
                      </span>
                    )}
                    {m.sets && m.sets.length > 0 && (
                      <span style={{ marginLeft: "0.5rem", fontSize: "0.9rem" }}>
                        {m.sets.map((s) => (
                          <span key={s.set_number} style={{ marginRight: "0.35rem" }}>
                            {s.reg1_score}×{s.reg2_score}
                          </span>
                        ))}
                      </span>
                    )}
                    {pending && (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{ marginLeft: "0.5rem" }}
                        disabled={busyMatchId === m.id}
                        onClick={() => onOpenSetForm(m)}
                      >
                        {busyMatchId === m.id ? "…" : "Registrar sets"}
                      </button>
                    )}
                  </li>
                );
              })}
          </ul>
        </div>
      ))}

      {openGroupMatch && (
        <div style={{ marginTop: "1rem" }}>
          <MatchSetResultForm
            tournament={tournament}
            match={toBracketMatch(openGroupMatch, tournament.id)}
            busy={busyMatchId === openGroupMatch.id}
            onCancel={onCloseSetForm}
            onSubmit={async (sets) => {
              await onSubmitSets(openGroupMatch, sets);
            }}
          />
        </div>
      )}
    </div>
  );
}
