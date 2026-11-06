-- v583 — lo que faltaba de la IA en inglés: las noticias (las traduce ia_gemini.traducir_pendientes) y el motivo del Pulso
alter table public.ia_analisis add column if not exists noticias_en text;
alter table public.pulso_ia add column if not exists motivo_en text;
