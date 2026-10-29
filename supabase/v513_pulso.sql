-- v513 — PULSO SHARPICKS: abrir el Pulso completo de UN partido con monedas, y el historial público de lo que
-- dijo el Pulso y lo que salió (transparencia).

-- 1. Pulso abierto con monedas, por partido («A vs B|AAAA-MM-DD», la misma clave que la página).
create table if not exists public.pulso_desbloqueos (
  usuario uuid not null references auth.users (id) on delete cascade,
  partido text not null,
  monedas int not null default 0,
  creado  timestamptz not null default now(),
  primary key (usuario, partido)
);
alter table public.pulso_desbloqueos enable row level security;
drop policy if exists "cada quien sus pulsos" on public.pulso_desbloqueos;
create policy "cada quien sus pulsos" on public.pulso_desbloqueos for select to authenticated using (auth.uid() = usuario);
revoke all on public.pulso_desbloqueos from anon, authenticated;
grant select on public.pulso_desbloqueos to authenticated;
grant all on public.pulso_desbloqueos to service_role;

insert into public.ajustes (clave, valor) values ('precio_pulso', '2') on conflict (clave) do nothing;

create or replace function public.desbloquear_pulso(p_partido text) returns text
language plpgsql security definer set search_path = public as $$
declare precio int; saldo int; es_admin boolean;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  if coalesce(trim(p_partido), '') = '' or length(p_partido) > 200 then return 'no existe'; end if;
  if public.es_pro() or exists (select 1 from public.pulso_desbloqueos where usuario = auth.uid() and partido = p_partido) then
    return 'ok';
  end if;
  select monedas, admin into saldo, es_admin from public.perfiles where id = auth.uid() for update;
  precio := case when es_admin then 0 else coalesce((select valor::int from public.ajustes where clave = 'precio_pulso'), 2) end;
  if coalesce(saldo, 0) < precio then return 'sin monedas'; end if;
  update public.perfiles set monedas = monedas - precio where id = auth.uid();
  insert into public.pulso_desbloqueos (usuario, partido, monedas) values (auth.uid(), p_partido, precio);
  if precio > 0 then
    insert into public.movimientos (usuario, cantidad, motivo) values (auth.uid(), -precio, 'pulso ' || left(p_partido, 120));
  end if;
  return 'ok';
end $$;
revoke all on function public.desbloquear_pulso(text) from public, anon;
grant execute on function public.desbloquear_pulso(text) to authenticated;

-- 2. Historial del Pulso: una lectura por partido, mercado y minuto de corte (60' y 70'), con el resultado al
--    pitido. Lo llena `pulso_historial.py` con la MISMA cuenta que la página; nadie lo retoca.
create table if not exists public.pulso_historial (
  partido   text not null,
  fecha     date not null,
  liga      text,
  minuto    int not null,
  mercado   text not null,
  marcador  text,
  prob      numeric(4,3) not null,
  acierto   boolean,
  creado    timestamptz not null default now(),
  primary key (partido, fecha, minuto, mercado)
);
alter table public.pulso_historial enable row level security;
drop policy if exists "todos leen el pulso" on public.pulso_historial;
create policy "todos leen el pulso" on public.pulso_historial for select using (true);
revoke all on public.pulso_historial from anon, authenticated;
grant select on public.pulso_historial to anon, authenticated;
grant all on public.pulso_historial to service_role;
