-- v533 — la «mejor jugada» de la IA rehecha ~2 h antes del partido (barrido 29-oct: +20 pts, p5 +8) se enseña en la
-- tarjeta. Columnas aparte para no tocar la medición del análisis principal (la de 2 h se mide en ia_ventanas).
alter table public.ia_analisis add column if not exists mejor_2h text;
alter table public.ia_analisis add column if not exists prob_mejor_2h numeric;
