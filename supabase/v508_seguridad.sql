-- v508 — AUDITORÍA DE SEGURIDAD (28-oct-2026). Lo que se encontró y se cierra aquí:
--
--  1. canjear_codigo sin límite: con un script se podían probar códigos sin parar. Ahora: 10 códigos
--     equivocados por hora y cuenta → «demasiados intentos».
--  2. Permisos de escritura de más: anon/authenticated tenían INSERT/UPDATE/DELETE en casi todas las
--     tablas. RLS ya lo frenaba (no hay política de escritura), pero si un día alguien añade una política
--     amplia, quedaría abierto. Se quitan; se dejan sólo los que usa la página (seguidos, ia_calificaciones
--     y las columnas propias de perfiles, que ya van por columna).
--  3. ia_medicion pasa a SECURITY INVOKER: medido, un anónimo ve lo mismo (72 filas idénticas). Las otras
--     cuatro siguen definer A PROPÓSITO: ia_aciertos (como invoker perdía «analizados»/«esperando
--     resultado», que la página enseña), ia_disponibles, seguidores y telegram_publicados sólo dan conteos,
--     nombres de partido o ids (con HMAC desde v508), nunca contenido de pago.
--  4. finanzas.set_updated_at con search_path variable.

-- 1 ─────────────────────────────────────────────────────────────────────────────────────────────
create table if not exists public.codigos_intentos (
  usuario uuid not null,
  creado  timestamptz not null default now()
);
create index if not exists codigos_intentos_usuario on public.codigos_intentos (usuario, creado desc);
alter table public.codigos_intentos enable row level security;      -- sin políticas: nadie lo lee de fuera
revoke all on public.codigos_intentos from anon, authenticated;
grant all on public.codigos_intentos to service_role;

create or replace function public.canjear_codigo(c text) returns text
language plpgsql security definer set search_path = public as $$
declare r public.codigos_regalo;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  if (select count(*) from public.codigos_intentos i
       where i.usuario = auth.uid() and i.creado > now() - interval '1 hour') >= 10 then
    return 'demasiados intentos';
  end if;
  select * into r from public.codigos_regalo where codigo = upper(trim(c)) for update;
  if not found then
    insert into public.codigos_intentos (usuario) values (auth.uid());
    return 'no existe';
  end if;
  if r.usado_por = auth.uid() then return 'ok'; end if;           -- v499: el código ya es tuyo
  if r.usado_por is not null then
    insert into public.codigos_intentos (usuario) values (auth.uid());
    return 'ya usado';
  end if;
  update public.codigos_regalo set usado_por = auth.uid(), usado = now() where codigo = r.codigo;
  update public.perfiles set plan = 'pro',
         plan_hasta = greatest(coalesce(plan_hasta, now()), now()) + make_interval(days => r.dias)
   where id = auth.uid();
  insert into public.movimientos (usuario, cantidad, motivo) values (auth.uid(), 0, 'codigo ' || r.codigo);
  return 'ok';
end $$;
revoke all on function public.canjear_codigo(text) from public, anon;
grant execute on function public.canjear_codigo(text) to authenticated;

-- 2 ─────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare t record;
begin
  for t in select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = 'public' and c.relkind in ('r', 'v', 'm', 'p') loop
    execute format('revoke insert, update, delete, truncate, references, trigger on public.%I from anon', t.relname);
    if t.relname not in ('seguidos', 'ia_calificaciones', 'perfiles') then
      execute format('revoke insert, update, delete, truncate, references, trigger on public.%I from authenticated', t.relname);
    end if;
  end loop;
end $$;
-- perfiles: sólo las columnas que la página cambia (ya era así; se deja escrito)
revoke insert, delete, truncate, references, trigger on public.perfiles from authenticated;
grant update (usuario, nombre, deportes, ligas) on public.perfiles to authenticated;

-- 3 ─────────────────────────────────────────────────────────────────────────────────────────────
alter view public.ia_medicion set (security_invoker = true);

-- 4 ─────────────────────────────────────────────────────────────────────────────────────────────
do $$ begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'finanzas' and p.proname = 'set_updated_at') then
    alter function finanzas.set_updated_at() set search_path = pg_catalog, finanzas;
  end if;
end $$;
