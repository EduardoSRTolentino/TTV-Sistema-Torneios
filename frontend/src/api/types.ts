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

export interface BracketMatch {
  id: number;
  tournament_id: number;
  round_number: number;
  position_in_round: number;
  reg1_id: number | null;
  reg2_id: number | null;
  winner_reg_id: number | null;
  next_match_id: number | null;
  round_label?: string;
  reg1_display?: string;
  reg2_display?: string;
  winner_display?: string | null;
}
