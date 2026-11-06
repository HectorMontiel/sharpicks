-- v582 — La app también va en inglés: el análisis de la IA en los dos idiomas (los motivos viajan dentro de `veredictos`).
alter table public.ia_analisis add column if not exists analisis_en text;
