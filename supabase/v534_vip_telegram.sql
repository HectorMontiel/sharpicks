-- v534 — EL GRUPO VIP DE TELEGRAM, CON LLAVE. El usuario: «que el bot apruebe quién puede entrar al VIP: no se va a poder
-- tener acceso si no tienes VIP; el bot tiene que verificar en la aplicación si es o no VIP… y si se le acaba la
-- suscripción, que ya le llegue gratis».
--   · el enlace del grupo pide permiso (creates_join_request); el bot (`telegram-bot`) lo aprueba sólo si ese Telegram
--     está ligado a una cuenta VIP vigente, y si no, lo rechaza y le dice qué hacer;
--   · cada pasada (telegram_canales.py) saca del grupo a quien se le acabó el VIP y le avisa;
--   · los avisos personales ya miran el VIP en el momento (alertas_destinos / telegram_ligados).

alter table public.telegram_usuarios add column if not exists en_vip boolean not null default false;

-- ¿este chat de Telegram es de una cuenta VIP vigente? (y de quién)
create or replace function public.telegram_quien(p_chat bigint) returns table (usuario uuid, vip boolean)
language sql stable security definer set search_path = public as $$
  select t.usuario, coalesce(p.admin, false) or (p.plan = 'pro' and (p.plan_hasta is null or p.plan_hasta > now()))
  from public.telegram_usuarios t left join public.perfiles p on p.id = t.usuario
  where t.chat = p_chat
$$;
-- los que están en el grupo VIP y ya no son VIP (para sacarlos)
create or replace function public.telegram_vip_vencidos() returns table (usuario uuid, chat bigint)
language sql stable security definer set search_path = public as $$
  select t.usuario, t.chat
  from public.telegram_usuarios t left join public.perfiles p on p.id = t.usuario
  where t.en_vip and t.chat is not null
    and not (coalesce(p.admin, false) or (p.plan = 'pro' and (p.plan_hasta is null or p.plan_hasta > now())))
$$;
revoke all on function public.telegram_quien(bigint) from public, anon, authenticated;
revoke all on function public.telegram_vip_vencidos() from public, anon, authenticated;
grant execute on function public.telegram_quien(bigint) to service_role;
grant execute on function public.telegram_vip_vencidos() to service_role;
