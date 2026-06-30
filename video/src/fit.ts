// Encolhe a fonte quando o texto é longo, pra nunca estourar a largura.
// `ideal` = nº de caracteres que cabe no tamanho `base`; acima disso, escala 1/len.
export const fitSize = (text: string, base: number, ideal: number, floor = base * 0.4) =>
  Math.max(floor, Math.min(base, (base * ideal) / Math.max(ideal, (text || "").length)));
