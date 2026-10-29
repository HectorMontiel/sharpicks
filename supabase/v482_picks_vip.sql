-- v482 — LO DEL VIP SÓLO PARA EL VIP.
-- Los jugadores (anota, a puerta 1+/2+) y las líneas por estadística con el parley viajaban en
-- `picks.jug` / `picks.ctx.lin` y en datos/hoy.json, que lee cualquiera: la página los tapaba, pero se
-- veían con las herramientas del navegador. Ahora van a `picks_vip`, que sólo lee quien es VIP
-- (o administrador: `es_pro()`). En lo público queda `vip_hay` para enseñar el 🔒.

-- 1) antes de publicar el exportador nuevo
create table if not exists public.picks_vip (
  clave text primary key,                  -- 'AAAA-MM-DD|Local vs Visita'
  fecha date not null,
  partido text not null,
  jug jsonb,
  lin jsonb,
  actualizado timestamptz not null default now()
);
create index if not exists picks_vip_fecha on public.picks_vip (fecha);
alter table public.picks_vip enable row level security;
drop policy if exists "sólo el VIP" on public.picks_vip;
create policy "sólo el VIP" on public.picks_vip for select to authenticated using (public.es_pro());
revoke all on public.picks_vip from anon, authenticated;
grant select on public.picks_vip to authenticated;
grant all on public.picks_vip to service_role;

alter table public.picks add column if not exists vip_hay boolean;

-- 2) después de la primera pasada del exportador nuevo: lo que ya estaba a la vista
update public.picks set vip_hay = true where jug is not null or ctx ? 'lin';
update public.picks set jug = null where jug is not null;
update public.picks set ctx = ctx - 'lin' where ctx ? 'lin';
