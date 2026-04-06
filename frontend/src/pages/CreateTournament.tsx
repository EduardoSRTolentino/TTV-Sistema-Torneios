import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "@/api/client";

export function CreateTournament() {
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [game_format, setGameFormat] = useState<"singles" | "doubles">("singles");
  const [max_participants, setMaxParticipants] = useState(32);
  const [deadline, setDeadline] = useState("");
  const [matchBestOf, setMatchBestOf] = useState(3);
  const [matchPointsPerSet, setMatchPointsPerSet] = useState(11);
  const [disputeThird, setDisputeThird] = useState(false);
  const [bracketFormat, setBracketFormat] = useState<"knockout" | "group_knockout">("knockout");
  const [groupSize, setGroupSize] = useState(4);
  const [qualifiedPerGroup, setQualifiedPerGroup] = useState(2);
  const [autoGenGroupsOnClose, setAutoGenGroupsOnClose] = useState(false);
  const [premioJson, setPremioJson] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      let ranking_premiacao: Record<string, number> | null = null;
      if (premioJson.trim()) {
        let parsed: unknown;
        try {
          parsed = JSON.parse(premioJson) as unknown;
        } catch {
          setErr("Premiação do ranking: JSON inválido.");
          return;
        }
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          setErr("Premiação do ranking: JSON deve ser um objeto, ex.: {\"1\": 100, \"2\": 50}");
          return;
        }
        ranking_premiacao = {};
        for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
          const n = Number(v);
          if (!Number.isFinite(n)) {
            setErr(`Premiação: valor inválido para a chave "${k}".`);
            return;
          }
          ranking_premiacao[k] = n;
        }
      }
      const t = await api.createTournament({
        title,
        description: description || undefined,
        game_format,
        bracket_format: bracketFormat,
        max_participants,
        registration_deadline: deadline ? new Date(deadline).toISOString() : null,
        match_best_of_sets: matchBestOf,
        match_points_per_set: matchPointsPerSet,
        dispute_third_place: disputeThird,
        ranking_premiacao,
        ...(bracketFormat === "group_knockout"
          ? {
              group_size: groupSize,
              qualified_per_group: qualifiedPerGroup,
              auto_generate_groups_on_close: autoGenGroupsOnClose,
            }
          : {}),
      });
      await api.openRegistration(t.id);
      nav(`/torneios/${t.id}`);
    } catch {
      setErr("Falha ao criar. Verifique JSON de premiação, se preenchido, e se você é organizador ou admin.");
    }
  }

  return (
    <div className="page-narrow">
      <h2 style={{ marginTop: 0 }}>Novo torneio</h2>
      <form className="card" onSubmit={onSubmit}>
        <div className="field">
          <label>Título</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
        </div>
        <div className="field">
          <label>Descrição</label>
          <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="field">
          <label>Formato</label>
          <select value={game_format} onChange={(e) => setGameFormat(e.target.value as "singles" | "doubles")}>
            <option value="singles">Individual</option>
            <option value="doubles">Duplas</option>
          </select>
        </div>
        <div className="field">
          <label>Formato do torneio</label>
          <select
            value={bracketFormat}
            onChange={(e) => setBracketFormat(e.target.value as "knockout" | "group_knockout")}
          >
            <option value="knockout">Mata-mata direto</option>
            <option value="group_knockout">Grupos + mata-mata</option>
          </select>
        </div>
        {bracketFormat === "group_knockout" && (
          <>
            <div className="field">
              <label>Tamanho do grupo</label>
              <select value={groupSize} onChange={(e) => setGroupSize(Number(e.target.value))}>
                <option value={3}>3 jogadores</option>
                <option value={4}>4 jogadores</option>
              </select>
            </div>
            <div className="field">
              <label>Classificados por grupo</label>
              <input
                type="number"
                min={1}
                max={8}
                value={qualifiedPerGroup}
                onChange={(e) => setQualifiedPerGroup(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>
                <input
                  type="checkbox"
                  checked={autoGenGroupsOnClose}
                  onChange={(e) => setAutoGenGroupsOnClose(e.target.checked)}
                />{" "}
                Gerar grupos automaticamente ao encerrar inscrições
              </label>
            </div>
          </>
        )}
        <div className="field">
          <label>Máximo de participantes</label>
          <input
            type="number"
            min={2}
            max={512}
            value={max_participants}
            onChange={(e) => setMaxParticipants(Number(e.target.value))}
          />
        </div>
        <div className="field">
          <label>Melhor de (sets por partida)</label>
          <select
            className="select"
            value={matchBestOf}
            onChange={(e) => setMatchBestOf(Number(e.target.value))}
          >
            <option value={1}>1 set</option>
            <option value={3}>3 sets</option>
            <option value={5}>5 sets</option>
            <option value={7}>7 sets</option>
          </select>
        </div>
        <div className="field">
          <label>Pontos por set (ex.: 11)</label>
          <input
            type="number"
            min={1}
            max={50}
            value={matchPointsPerSet}
            onChange={(e) => setMatchPointsPerSet(Number(e.target.value) || 11)}
          />
          <small style={{ color: "var(--muted)", display: "block", marginTop: "0.25rem" }}>
            Diferença mínima de 2 pontos para vencer o set é fixa no sistema.
          </small>
        </div>
        <div className="field">
          <label>
            <input
              type="checkbox"
              checked={disputeThird}
              onChange={(e) => setDisputeThird(e.target.checked)}
            />{" "}
            Disputa de 3º lugar (partida entre perdedores da semifinal)
          </label>
        </div>
        <div className="field">
          <label>Pontos de ranking por colocação (JSON opcional)</label>
          <textarea
            rows={3}
            value={premioJson}
            onChange={(e) => setPremioJson(e.target.value)}
            placeholder='{"1": 100, "2": 50, "3": 25}'
          />
          <small style={{ color: "var(--muted)", display: "block", marginTop: "0.25rem" }}>
            Aplicado ao encerrar o torneio; empate no 3º (sem disputa) credita o mesmo valor a ambos.
          </small>
        </div>
        <div className="field">
          <label>Prazo de inscrição (opcional)</label>
          <input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
        </div>
        {err && <p className="error">{err}</p>}
        <button className="btn btn-primary" type="submit">
          Criar e abrir inscrições
        </button>
      </form>
    </div>
  );
}
