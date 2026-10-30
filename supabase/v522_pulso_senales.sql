-- v522 — LAS SEÑALES DEL PULSO, MEDIDAS. El usuario: «todas las que estén arriba de un 70 % (o el umbral que
-- consideres, alto) empiézalas a medir: cuáles sí se están cumpliendo, en Ver partido y en el historial».
-- Umbral 70 % (lo eligió el usuario; lo medido: 70-80 % salió 72-76 %) y que
-- aún pague (cuota justa ≥ 1,15). La función en la nube `pulso-vivo` apunta UNA señal por partido, mercado y marcador
-- la primera vez que cruza, con el minuto y los córners de ese momento; la marca ✅ en cuanto se cumple y ❌ si el
-- partido termina sin cumplirse. Nadie la retoca después.

create table if not exists public.pulso_senales (
  clave     text not null,                 -- «Fútbol|a / b|AAAA-MM-DD» (clavePartido de la página)
  partido   text not null,
  fecha     date not null,
  liga      text,
  mercado   text not null,                 -- gol, gol2, gol_l, gol_v, cor1, cor2, cor3
  marcador  text not null,                 -- al cruzar el umbral
  minuto    int not null,
  corners   int,
  prob      numeric(4,3) not null,
  ia        boolean not null default false, -- la que eligió «IA + modelo»
  acierto   boolean,
  cumplida_min int,                        -- el minuto en que se cumplió
  creado    timestamptz not null default now(),
  primary key (clave, mercado, marcador)
);
create index if not exists pulso_senales_fecha on public.pulso_senales (fecha);
alter table public.pulso_senales enable row level security;
revoke all on public.pulso_senales from anon, authenticated;
grant all on public.pulso_senales to service_role;

-- Lo que la página puede ver: todas las señales (de los últimos días), y el mercado de las que siguen en juego sólo
-- con VIP o con el Pulso de ese partido abierto; las ya calificadas, para todos (transparencia).
create or replace function public.pulso_senales_ver(p_desde date) returns table (
  clave text, partido text, fecha date, liga text, mercado text, marcador text, minuto int, corners int, prob numeric,
  ia boolean, acierto boolean, cumplida_min int)
language sql stable security definer set search_path = public as $$
  select s.clave, s.partido, s.fecha, s.liga,
    case when s.acierto is not null or (select public.es_pro())
           or exists (select 1 from public.pulso_desbloqueos d where d.usuario = (select auth.uid()) and d.partido = s.clave)
         then s.mercado end,
    s.marcador, s.minuto, s.corners,
    case when s.acierto is not null or (select public.es_pro())
           or exists (select 1 from public.pulso_desbloqueos d where d.usuario = (select auth.uid()) and d.partido = s.clave)
         then s.prob end,
    s.ia, s.acierto, s.cumplida_min
  from public.pulso_senales s
  where s.fecha >= p_desde
  order by s.creado desc
  limit 500
$$;
revoke all on function public.pulso_senales_ver(date) from public;
grant execute on function public.pulso_senales_ver(date) to anon, authenticated;

-- la tasa de todo lo calificado, por mercado (para el historial)
create or replace function public.pulso_senales_tasa() returns table (mercado text, ia boolean, n bigint, aciertos bigint, prob numeric)
language sql stable security definer set search_path = public as $$
  select mercado, ia, count(*), count(*) filter (where acierto), round(avg(prob), 3)
  from public.pulso_senales where acierto is not null group by mercado, ia
$$;
revoke all on function public.pulso_senales_tasa() from public;
grant execute on function public.pulso_senales_tasa() to anon, authenticated;
