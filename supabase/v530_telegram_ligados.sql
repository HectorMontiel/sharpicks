-- v530 — a quién se le avisa de SUS cosas (picks que sigue y combinadas que armó): todos los que ligaron Telegram,
-- tengan o no alertas elegidas. Sólo con la llave de servicio.
create or replace function public.telegram_ligados() returns table (usuario uuid, chat bigint, vip boolean)
language sql stable security definer set search_path = public as $$
  select t.usuario, t.chat,
    coalesce(p.admin, false) or (p.plan = 'pro' and (p.plan_hasta is null or p.plan_hasta > now()))
  from public.telegram_usuarios t left join public.perfiles p on p.id = t.usuario
  where t.chat is not null
$$;
revoke all on function public.telegram_ligados() from public, anon, authenticated;
grant execute on function public.telegram_ligados() to service_role;
