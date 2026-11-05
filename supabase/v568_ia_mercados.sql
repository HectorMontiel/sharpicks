-- v568 — La plantilla del análisis de cada deporte: los mercados que Playdoit ofrece en NHL, NBA, NFL, béisbol y tenis.
-- [{k: clave, t: nombre, v: texto, p: probabilidad}]. En fútbol queda vacía: su plantilla usa las columnas de siempre.
alter table public.ia_analisis add column if not exists mercados jsonb;
