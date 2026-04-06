export type UserRole = "admin" | "organizer" | "player";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
  rating?: number | null;
}

export type TournamentStatus =
  | "draft"
  | "registration_open"
  | "registration_closed"
  | "in_progress"
  | "completed";

export interface Tournament {
  id: number;
  title: string;
  description: string | null;
  organizer_id: number;
  game_format: "singles" | "doubles";
  bracket_format: "knockout" | "group_knockout";
  max_participants: number;
  registration_fee: number;
  prize: string | null;
  registration_deadline: string | null;
  match_best_of_sets: number;
  match_points_per_set: number;
  dispute_third_place: boolean;
  ranking_premiacao?: Record<string, number> | null;
  status: TournamentStatus;
  created_at: string;
  registrations_count: number;
}

export interface Registration {
  id: number;
  tournament_id: number;
  user_id: number;
  user_full_name: string;
  user_rating: number;
  partner_user_id: number | null;
  partner_full_name?: string | null;
  partner_rating?: number | null;
  created_at: string;
  bracket_seed_rating?: number | null;
}

export interface BracketMatchSetRow {
  set_number: number;
  reg1_score: number;
  reg2_score: number;
}

export interface BracketMatch {
  id: number;
  tournament_id: number;
  round_number: number;
  position_in_round: number;
  match_order?: number;
  bracket_round_key?: string | null;
  bracket_position?: number | null;
  reg1_id: number | null;
  reg2_id: number | null;
  winner_reg_id: number | null;
  next_match_id: number | null;
  status?: "pending" | "in_progress" | "finished";
  match_kind?: "knockout" | "third_place";
  round_label?: string;
  reg1_display?: string;
  reg2_display?: string;
  winner_display?: string | null;
  sets?: BracketMatchSetRow[];
}
