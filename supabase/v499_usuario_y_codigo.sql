-- v499 — EL USUARIO Y EL CÓDIGO DE REGALO, SIN FALSOS «YA EXISTE» / «NO EXISTE».
-- El usuario: «al registrarme pongo un nombre de usuario y me dice que ya existe, cosa que no existe» y
-- «me sale que ese código no existe». En los dos casos la acción SÍ se había hecho (el perfil quedó con
-- su usuario; el código se canjeó y la cuenta quedó VIP), pero la página se lo dijo al revés: el envío se
-- repetía (teclado + botón) y la 2.ª vez el nombre ya era SUYO o el código ya estaba usado POR ÉL.
-- 1) el nombre propio cuenta como libre para uno mismo
create or replace function public.usuario_libre(u text) returns boolean
language sql stable security definer set search_path = public as $$
  select u ~ '^[A-Za-z0-9_.]{3,20}$'
     and not exists (select 1 from public.perfiles where lower(usuario) = lower(u) and id is distinct from auth.uid());
$$;
grant execute on function public.usuario_libre(text) to anon, authenticated;

-- 2) canjear dos veces el mismo código desde la misma cuenta no es un error: ya es suyo
create or replace function public.canjear_codigo(c text) returns text
language plpgsql security definer set search_path = public as $$
declare r public.codigos_regalo;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  select * into r from public.codigos_regalo where codigo = upper(trim(c)) for update;
  if not found then return 'no existe'; end if;
  if r.usado_por = auth.uid() then return 'ok'; end if;
  if r.usado_por is not null then return 'ya usado'; end if;
  update public.codigos_regalo set usado_por = auth.uid(), usado = now() where codigo = r.codigo;
  update public.perfiles set plan = 'pro',
         plan_hasta = greatest(coalesce(plan_hasta, now()), now()) + make_interval(days => r.dias)
   where id = auth.uid();
  insert into public.movimientos (usuario, cantidad, motivo) values (auth.uid(), 0, 'codigo ' || r.codigo);
  return 'ok';
end $$;
revoke execute on function public.canjear_codigo(text) from public, anon;
grant execute on function public.canjear_codigo(text) to authenticated;
