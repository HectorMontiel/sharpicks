-- v521 — EL VIGILANTE DEL PULSO EN LA NUBE (el usuario: «no quiero tener mi compu encendida todo el tiempo»).
-- pg_cron llama a la función `pulso-vivo` cada 2 minutos, con una clave propia guardada en Vault. Las claves de
-- Telegram y Gemini también van cifradas en Vault: las copia de los secretos de GitHub el workflow «Claves a
-- Supabase» (guardar_secreto, sólo service_role) y sólo la función las lee (leer_secretos_pulso, sólo service_role).

create extension if not exists pg_cron;
create extension if not exists pg_net;

create or replace function public.guardar_secreto(p_nombre text, p_valor text) returns void
language plpgsql security definer set search_path = public, vault as $$
declare i uuid;
begin
  if p_nombre not in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_VIP', 'GEMINI_API_KEY') then raise exception 'no permitido'; end if;
  if coalesce(p_valor, '') = '' then return; end if;
  select id into i from vault.secrets where name = p_nombre;
  if i is null then perform vault.create_secret(p_valor, p_nombre);
  else perform vault.update_secret(i, p_valor, p_nombre); end if;
end $$;
revoke all on function public.guardar_secreto(text, text) from public, anon, authenticated;
grant execute on function public.guardar_secreto(text, text) to service_role;

create or replace function public.leer_secretos_pulso() returns table (nombre text, valor text)
language sql stable security definer set search_path = public, vault as $$
  select name::text, decrypted_secret::text from vault.decrypted_secrets
  where name in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_VIP', 'GEMINI_API_KEY', 'pulso_cron')
$$;
revoke all on function public.leer_secretos_pulso() from public, anon, authenticated;
grant execute on function public.leer_secretos_pulso() to service_role;

-- la clave con la que pg_cron llama a la función (nadie más puede dispararla)
do $$ begin
  if not exists (select 1 from vault.secrets where name = 'pulso_cron') then
    perform vault.create_secret(encode(extensions.gen_random_bytes(24), 'hex'), 'pulso_cron');
  end if;
end $$;

-- cada 2 minutos; sin partidos en juego la función termina en un instante
select cron.unschedule('pulso-vivo') where exists (select 1 from cron.job where jobname = 'pulso-vivo');
select cron.schedule('pulso-vivo', '*/2 * * * *', $cron$
  select net.http_post(
    url := 'https://lyfmyehvfywnjasinbne.supabase.co/functions/v1/pulso-vivo',
    headers := jsonb_build_object('Content-Type', 'application/json',
      'x-pulso-clave', (select decrypted_secret from vault.decrypted_secrets where name = 'pulso_cron')),
    body := '{}'::jsonb,
    timeout_milliseconds := 120000)
$cron$);
