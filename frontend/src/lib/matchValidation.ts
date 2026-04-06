/** Espelha regras do backend: set até `pointsPerSet`, vitória com diferença mínima de 2. */
const SET_MIN_LEAD = 2;

export function isValidTerminalSet(
  scoreA: number,
  scoreB: number,
  pointsPerSet: number,
  minLead: number = SET_MIN_LEAD,
): boolean {
  if (scoreA < 0 || scoreB < 0 || scoreA === scoreB) return false;
  const hi = Math.max(scoreA, scoreB);
  const lo = Math.min(scoreA, scoreB);
  const diff = hi - lo;
  if (diff < minLead) return false;
  if (hi < pointsPerSet) return false;
  if (lo >= pointsPerSet - 1) return true;
  return hi === pointsPerSet && diff >= minLead;
}

export type SetInputRow = { set_number: number; reg1_score: number; reg2_score: number };

export function validateMatchSets(
  reg1Id: number,
  reg2Id: number,
  rows: SetInputRow[],
  bestOfSets: number,
  pointsPerSet: number,
): { ok: true; winnerRegId: number } | { ok: false; message: string } {
  if (reg1Id === reg2Id) return { ok: false, message: "Partida inválida (jogadores duplicados)." };
  if (!rows.length) return { ok: false, message: "Informe pelo menos um set." };
  const ordered = [...rows].sort((a, b) => a.set_number - b.set_number);
  const nums = ordered.map((r) => r.set_number);
  if (new Set(nums).size !== nums.length) return { ok: false, message: "Número de set repetido." };
  if (nums.some((n) => n < 1)) return { ok: false, message: "Número de set inválido." };
  const need = Math.floor((bestOfSets + 1) / 2);
  let w1 = 0;
  let w2 = 0;
  for (let i = 0; i < ordered.length; i++) {
    const row = ordered[i];
    if (!isValidTerminalSet(row.reg1_score, row.reg2_score, pointsPerSet)) {
      return {
        ok: false,
        message: `Set ${row.set_number} inválido (precisa fechar em ${pointsPerSet} com diferença mínima ${SET_MIN_LEAD}).`,
      };
    }
    if (row.reg1_score > row.reg2_score) w1 += 1;
    else w2 += 1;
    if (w1 >= need || w2 >= need) {
      if (i !== ordered.length - 1) {
        return { ok: false, message: "Remova sets após o vencedor já estar decidido." };
      }
      break;
    }
  }
  if (w1 < need && w2 < need) {
    return { ok: false, message: "Resultado incompleto: ninguém atingiu os sets necessários." };
  }
  if (w1 >= need && w2 >= need) return { ok: false, message: "Placar inconsistente." };
  return { ok: true, winnerRegId: w1 >= need ? reg1Id : reg2Id };
}
