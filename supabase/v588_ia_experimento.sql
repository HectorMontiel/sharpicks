-- v588 — el experimento de la IA a ciegas: lo que lee en las noticias de cada pick ya jugado, sin ver cuota ni probabilidad.
-- Sólo lo escribe y lo lee el servidor: nunca lo ve un usuario. Se mide si suma a la cuota antes de enseñar nada.
create table if not exists public.ia_experimento (
  version text not null,
  fecha date not null,
  partido text not null,
  apuesta text not null,
  impacto integer,
  factores text[],
  nota text,
  modelo text,
  creado timestamptz default now(),
  primary key (version, fecha, partido, apuesta)
);
alter table public.ia_experimento enable row level security;
revoke all on table public.ia_experimento from public, anon, authenticated;
grant all on public.ia_experimento to service_role;
