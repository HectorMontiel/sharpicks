-- v527 — AVISOS PERSONALES POR TELEGRAM. El usuario: «¿hay forma de que desde SharPicks un usuario ligue que le manden
-- alertas de algo en específico al Telegram? Partido en específico, sólo algún deporte… si no existe, hay que crearlo».
--   1. Ligar: la app pide un código de un solo uso (telegram_codigo) y abre t.me/<bot>?start=<código>; el bot (función
--      `telegram-bot`, webhook) lo canjea y guarda el chat del usuario. Nadie más ve el chat.
--   2. Elegir: deportes («picks de NBA»), el Pulso en vivo, o un partido en específico (la campana de Ver partido).
--   3. Recibir: la nube (pulso-vivo) y el sitio (telegram_canales.py) le mandan lo suyo por mensaje directo. Lo VIP
--      sólo al VIP (o al que abrió ese Pulso con monedas); al resto, el aviso con candado para desbloquear.

create table if not exists public.telegram_usuarios (
  usuario      uuid primary key references auth.users (id) on delete cascade,
  chat         bigint unique,
  codigo       text unique,
  codigo_hasta timestamptz,
  ligado       timestamptz
);
alter table public.telegram_usuarios enable row level security;
revoke all on public.telegram_usuarios from anon, authenticated;
grant all on public.telegram_usuarios to service_role;

create table if not exists public.alertas_tg (
  usuario uuid not null references auth.users (id) on delete cascade,
  tipo    text not null check (tipo in ('deporte', 'partido', 'pulso')),
  valor   text not null check (length(valor) between 1 and 200),
  creado  timestamptz not null default now(),
  primary key (usuario, tipo, valor)
);
alter table public.alertas_tg enable row level security;
drop policy if exists "cada quien sus alertas" on public.alertas_tg;
create policy "cada quien sus alertas" on public.alertas_tg for all to authenticated
  using ((select auth.uid()) = usuario) with check ((select auth.uid()) = usuario);
revoke all on public.alertas_tg from anon, authenticated;
grant select, insert, delete on public.alertas_tg to authenticated;
grant all on public.alertas_tg to service_role;

-- el código de un solo uso para ligar (15 minutos)
create or replace function public.telegram_codigo() returns text
language plpgsql security definer set search_path = public, extensions as $$
declare c text;
begin
  if auth.uid() is null then return null; end if;
  c := upper(substr(encode(extensions.gen_random_bytes(8), 'hex'), 1, 10));
  insert into public.telegram_usuarios (usuario, codigo, codigo_hasta) values (auth.uid(), c, now() + interval '15 minutes')
  on conflict (usuario) do update set codigo = excluded.codigo, codigo_hasta = excluded.codigo_hasta;
  return c;
end $$;
-- ¿estoy ligado? (sin decir el chat)
create or replace function public.telegram_ligado() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.telegram_usuarios where usuario = auth.uid() and chat is not null)
$$;
create or replace function public.telegram_desligar() returns void
language sql security definer set search_path = public as $$
  update public.telegram_usuarios set chat = null, ligado = null where usuario = auth.uid()
$$;
revoke all on function public.telegram_codigo() from public, anon;
revoke all on function public.telegram_ligado() from public, anon;
revoke all on function public.telegram_desligar() from public, anon;
grant execute on function public.telegram_codigo() to authenticated;
grant execute on function public.telegram_ligado() to authenticated;
grant execute on function public.telegram_desligar() to authenticated;

-- la clave con la que Telegram firma cada llamada al webhook (X-Telegram-Bot-Api-Secret-Token)
do $$ begin
  if not exists (select 1 from vault.secrets where name = 'telegram_webhook') then
    perform vault.create_secret(encode(extensions.gen_random_bytes(24), 'hex'), 'telegram_webhook');
  end if;
end $$;
create or replace function public.leer_secretos_pulso() returns table (nombre text, valor text)
language sql stable security definer set search_path = public, vault as $$
  select name::text, decrypted_secret::text from vault.decrypted_secrets
  where name in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_VIP', 'TELEGRAM_CHAT_GRATIS', 'GEMINI_API_KEY', 'pulso_cron', 'telegram_webhook')
$$;
revoke all on function public.leer_secretos_pulso() from public, anon, authenticated;
grant execute on function public.leer_secretos_pulso() to service_role;

-- quién recibe qué (para la nube y el sitio, con la llave de servicio): el chat, si es VIP y sus alertas
create or replace function public.alertas_destinos() returns table (usuario uuid, chat bigint, vip boolean, tipo text, valor text)
language sql stable security definer set search_path = public as $$
  select t.usuario, t.chat,
    coalesce(p.admin, false) or (p.plan = 'pro' and (p.plan_hasta is null or p.plan_hasta > now())),
    a.tipo, a.valor
  from public.telegram_usuarios t
  join public.alertas_tg a on a.usuario = t.usuario
  left join public.perfiles p on p.id = t.usuario
  where t.chat is not null
$$;
revoke all on function public.alertas_destinos() from public, anon, authenticated;
grant execute on function public.alertas_destinos() to service_role;
