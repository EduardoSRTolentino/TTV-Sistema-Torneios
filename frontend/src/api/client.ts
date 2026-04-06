import axios from "axios";
import type { BracketMatch, Registration, Tournament, User, UserRole } from "./types";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    localStorage.setItem("ttv_token", token);
  } else {
    delete api.defaults.headers.common.Authorization;
    localStorage.removeItem("ttv_token");
  }
}

const saved = localStorage.getItem("ttv_token");
if (saved) setAuthToken(saved);

export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
  setAuthToken(data.access_token);
  return data;
}

export async function register(payload: { email: string; password: string; full_name: string }) {
  const { data } = await api.post<User>("/auth/register", payload);
  return data;
}

export async function me() {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function listTournaments() {
  const { data } = await api.get<Tournament[]>("/tournaments");
  return data;
}

export async function getTournament(id: number) {
  const { data } = await api.get<Tournament>(`/tournaments/${id}`);
  return data;
}

export async function createTournament(payload: {
  title: string;
  description?: string;
  game_format: "singles" | "doubles";
  bracket_format: "knockout" | "group_knockout";
  max_participants: number;
  registration_fee?: number;
  prize?: string | null;
  registration_deadline?: string | null;
  match_best_of_sets?: number;
  match_points_per_set?: number;
  dispute_third_place?: boolean;
  ranking_premiacao?: Record<string, number> | null;
}) {
  const { data } = await api.post<Tournament>("/tournaments", payload);
  return data;
}

export async function updateTournament(
  id: number,
  payload: {
    title: string;
    max_participants: number;
    registration_fee: number;
    prize?: string | null;
    registration_deadline?: string | null;
    match_best_of_sets?: number;
    match_points_per_set?: number;
    dispute_third_place?: boolean;
    ranking_premiacao?: Record<string, number> | null;
  },
) {
  const { data } = await api.patch<Tournament>(`/tournaments/${id}`, payload);
  return data;
}

export async function openRegistration(id: number) {
  const { data } = await api.post<Tournament>(`/tournaments/${id}/abrir-inscricoes`);
  return data;
}

export async function closeRegistration(id: number) {
  const { data } = await api.post<Tournament>(`/tournaments/${id}/fechar-inscricoes`);
  return data;
}

/** Encerra inscrições (equivalente ao POST legado, preferido para novas telas). */
export async function patchCloseRegistrations(id: number) {
  const { data } = await api.patch<Tournament>(`/tournaments/${id}/close-registrations`);
  return data;
}

export async function startTournament(id: number) {
  const { data } = await api.patch<Tournament>(`/tournaments/${id}/start`);
  return data;
}

export async function registerInTournament(id: number, partner_email?: string) {
  const { data } = await api.post<Registration>(`/tournaments/${id}/inscricao`, {
    partner_email: partner_email || null,
  });
  return data;
}

export async function listRegistrations(id: number) {
  const { data } = await api.get<Registration[]>(`/tournaments/${id}/inscricoes`);
  return data;
}

export async function generateBracket(id: number) {
  const { data } = await api.post<BracketMatch[]>(`/tournaments/${id}/gerar-chaveamento`);
  return data;
}

export async function getBracket(id: number) {
  const { data } = await api.get<BracketMatch[]>(`/tournaments/${id}/chaveamento`);
  return data;
}

export async function listRanking() {
  const { data } = await api.get<
    Array<{
      user_id: number;
      full_name: string;
      rating: number;
      ranking_points?: number;
      combined_score?: number;
      games_played: number;
    }>
  >("/ranking");
  return data;
}

export async function setWinner(matchId: number, winner_registration_id: number) {
  const { data } = await api.post<BracketMatch>(`/tournaments/partidas/${matchId}/vencedor`, {
    winner_registration_id,
  });
  return data;
}

export async function submitMatchResult(
  matchId: number,
  sets: Array<{ set_number: number; reg1_score: number; reg2_score: number }>,
) {
  const { data } = await api.post<BracketMatch>(`/tournaments/partidas/${matchId}/resultado`, { sets });
  return data;
}

export async function listUsers() {
  const { data } = await api.get<User[]>("/users");
  return data;
}

export async function setUserRole(userId: number, role: UserRole) {
  const { data } = await api.patch<User>(`/users/${userId}/role`, { role });
  return data;
}

export async function getSystemSettings() {
  const { data } = await api.get<{ id: number; initial_ranking: number }>("/system-settings");
  return data;
}

export async function patchSystemSettings(payload: { initial_ranking: number }) {
  const { data } = await api.patch<{ id: number; initial_ranking: number }>("/system-settings", payload);
  return data;
}

export async function patchUserRanking(userId: number, ranking: number) {
  const { data } = await api.patch<User>(`/users/${userId}/ranking`, { ranking });
  return data;
}

export { api };
