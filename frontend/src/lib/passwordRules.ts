/** Alinhado a `backend/app/password_validation.py` */

const MIN = 8;
const MAX = 128;

export function passwordValidationError(password: string): string | null {
  if (password.length < MIN) {
    return `A senha deve ter pelo menos ${MIN} caracteres.`;
  }
  if (password.length > MAX) {
    return `A senha deve ter no máximo ${MAX} caracteres.`;
  }
  if (!/[A-Z]/.test(password)) {
    return "Inclua pelo menos uma letra maiúscula.";
  }
  if (!/[a-z]/.test(password)) {
    return "Inclua pelo menos uma letra minúscula.";
  }
  if (!/\d/.test(password)) {
    return "Inclua pelo menos um número.";
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    return "Inclua pelo menos um caractere especial (ex.: ! @ #).";
  }
  return null;
}

export const PASSWORD_HINT =
  "Mínimo 8 caracteres, com maiúscula, minúscula, número e caractere especial.";
