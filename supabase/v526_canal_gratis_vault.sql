-- v526 — el canal gratis también recibe el gancho del Pulso («el Pulso detectó algo… desbloquéalo»): su id va a Vault
-- como los demás (lo copia el workflow «Claves a Supabase»), y la función en la nube lo lee.
create or replace function public.guardar_secreto(p_nombre text, p_valor text) returns void
language plpgsql security definer set search_path = public, vault as $$
declare i uuid;
begin
  if p_nombre not in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_VIP', 'TELEGRAM_CHAT_GRATIS', 'GEMINI_API_KEY') then raise exception 'no permitido'; end if;
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
  where name in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_VIP', 'TELEGRAM_CHAT_GRATIS', 'GEMINI_API_KEY', 'pulso_cron')
$$;
revoke all on function public.leer_secretos_pulso() from public, anon, authenticated;
grant execute on function public.leer_secretos_pulso() to service_role;
