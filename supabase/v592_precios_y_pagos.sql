-- v592 — PRECIOS, MONEDAS, FUNDADORES Y EL LIBRO DE COBROS.
-- Precios (quien ya está suscrito conserva el suyo; Stripe y Mercado Pago lo guardan al suscribirse):
--   VIP 189 → 199 · semestral 919 → 999 · fundador 129 → 149, y 20 lugares en vez de 50.
--   monedas: 50 = 39 → 49 · 100 = 65 → 85 · 220 = 129 → 169 · 500 = 249 → 329 · regalo al registrarse 20 → 15.
update public.ajustes set valor = '199' where clave = 'precio_mensual';
update public.ajustes set valor = '149' where clave = 'precio_fundador';
update public.ajustes set valor = '999' where clave = 'precio_semestral';
update public.ajustes set valor = '20' where clave = 'lugares_fundador';
update public.ajustes set valor = '15' where clave = 'monedas_bienvenida';
update public.paquetes set precio = 49 where id = 'prueba';
update public.paquetes set precio = 85 where id = 'popular';
update public.paquetes set precio = 169 where id = 'pro';
update public.paquetes set precio = 329 where id = 'mega';

-- los lugares salen de ajustes, no de un número escrito en la función
create or replace function public.lugares_fundador()
returns integer language sql stable security definer set search_path to 'public' as $$
  select greatest(0, coalesce((select valor::int from public.ajustes where clave = 'lugares_fundador'), 20) - (
    select count(distinct usuario)::int from public.suscripciones
     where fundador and (estado in ('authorized', 'pagado') or (estado = 'pending' and actualizado > now() - interval '30 minutes'))));
$$;

-- cada cobro, uno por uno: suscripciones sólo guarda el último estado. Al borrar una cuenta el cobro queda sin identificar.
create table if not exists public.pagos (
  id text primary key,
  fuente text not null,
  tipo text not null,
  usuario uuid references auth.users (id) on delete set null,
  bruto numeric not null,
  comision numeric,
  reembolsado numeric not null default 0,
  pagado timestamptz not null,
  creado timestamptz default now()
);
create index if not exists pagos_pagado on public.pagos (pagado);
alter table public.pagos enable row level security;
revoke all on table public.pagos from public, anon, authenticated;
grant all on public.pagos to service_role;

-- qué mes ya se mandó, para no repetirlo
create table if not exists public.fiscal_envios (
  clave text primary key,
  enviado timestamptz default now()
);
alter table public.fiscal_envios enable row level security;
revoke all on table public.fiscal_envios from public, anon, authenticated;
grant all on public.fiscal_envios to service_role;

-- lo que ya se cobró antes de este libro
insert into public.pagos (id, fuente, tipo, usuario, bruto, pagado)
select 'compra:' || id, case when id like 'stripe:%' then 'stripe' else 'mercadopago' end, 'monedas', usuario, precio, creado
from public.compras where estado = 'approved'
on conflict (id) do nothing;
