-- v589 — lo que leyó la IA en vivo, para poder revisarlo después (bajas y titulares)
alter table public.ia_experimento add column if not exists datos text;
