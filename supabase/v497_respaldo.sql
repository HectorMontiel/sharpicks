-- v497 — RESPALDO NOCTURNO. El plan gratis de Supabase no tiene respaldos automáticos: cada noche
-- `respaldo_base.py` (workflow `respaldo_base.yml`) baja todas las tablas de `public` con la clave de
-- servicio y, con esta función, las cuentas de `auth` (con su contraseña tal como la guarda Supabase,
-- cifrada con bcrypt), para poder restaurar sin pedir a nadie que cambie su contraseña. El paquete se
-- cifra antes de guardarse (el repositorio es público).
-- Sólo la llama la clave de servicio: ni anon ni authenticated.
create or replace function public.respaldo_auth()
returns jsonb
language sql
security definer
set search_path = auth, public
as $$
  select jsonb_build_object(
    'users', coalesce((select jsonb_agg(to_jsonb(u)) from auth.users u), '[]'::jsonb),
    'identities', coalesce((select jsonb_agg(to_jsonb(i)) from auth.identities i), '[]'::jsonb)
  );
$$;
revoke all on function public.respaldo_auth() from public, anon, authenticated;
grant execute on function public.respaldo_auth() to service_role;
