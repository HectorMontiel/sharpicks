-- v520 — PULSO · IA + MODELO: la mejor jugada en vivo de cada partido, elegida por Gemini SÓLO entre los mercados
-- que el Pulso midió (con su probabilidad), y liquidada al pitido para medirla. La escribe pulso_vivo.py (runner
-- del PC, cada 2 min). Se lee con VIP o con el Pulso del partido abierto con monedas; todos ven si hay una y la tasa.

create table if not exists public.pulso_ia (
  clave     text not null,                 -- «Fútbol|a / b|AAAA-MM-DD», la misma de pulso_desbloqueos
  partido   text not null,
  fecha     date not null,
  marcador  text not null,                 -- el marcador al recomendar: un gol después, se vuelve a preguntar
  minuto    int not null,
  mercado   text not null,                 -- gol, gol2, gol_l, gol_v, cor1, cor2, cor3
  prob      numeric(4,3) not null,         -- lo que dijo el modelo de ese mercado
  corners   int,                           -- córners al recomendar (para liquidar los de córners)
  motivo    text,
  modelo_ia text,
  acierto   boolean,
  creado    timestamptz not null default now(),
  primary key (clave, marcador)
);
create index if not exists pulso_ia_fecha on public.pulso_ia (fecha);
alter table public.pulso_ia enable row level security;
drop policy if exists "vip o pulso abierto" on public.pulso_ia;
create policy "vip o pulso abierto" on public.pulso_ia for select to authenticated using (
  (select public.es_pro())
  or exists (select 1 from public.pulso_desbloqueos d where d.usuario = (select auth.uid()) and d.partido = pulso_ia.clave));
revoke all on public.pulso_ia from anon, authenticated;
grant select on public.pulso_ia to authenticated;
grant all on public.pulso_ia to service_role;

-- quién tiene recomendación ahora (sin decir cuál) y la tasa de lo ya liquidado: para todos
create or replace function public.pulso_ia_hay(p_desde date) returns table (clave text, marcador text, minuto int)
language sql stable security definer set search_path = public as $$
  select clave, marcador, minuto from public.pulso_ia where fecha >= p_desde and acierto is null order by creado desc limit 200
$$;
create or replace function public.pulso_ia_tasa() returns table (n bigint, aciertos bigint)
language sql stable security definer set search_path = public as $$
  select count(*), count(*) filter (where acierto) from public.pulso_ia where acierto is not null
$$;
revoke all on function public.pulso_ia_hay(date) from public;
revoke all on function public.pulso_ia_tasa() from public;
grant execute on function public.pulso_ia_hay(date) to anon, authenticated;
grant execute on function public.pulso_ia_tasa() to anon, authenticated;
