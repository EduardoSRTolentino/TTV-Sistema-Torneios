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
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const t = await api.createTournament({
        title,
        description: description || undefined,
        game_format,
        bracket_format: "knockout",
        max_participants,
        registration_deadline: deadline ? new Date(deadline).toISOString() : null,
      });
      await api.openRegistration(t.id);
      nav(`/torneios/${t.id}`);
    } catch {
      setErr("Falha ao criar. Verifique se você é organizador ou admin.");
    }
  }

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
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
