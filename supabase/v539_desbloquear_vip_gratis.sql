-- v539 — un VIP nunca paga monedas por un pick. La prueba de pagos (29-oct) encontró que `desbloquear` cobraba
-- también al VIP si llegaba a llamarla (la página no le enseña el botón, pero nada en la base lo impedía).
-- Ahora el VIP vigente (es_pro) queda igual que el admin: se anota el desbloqueo a 0 monedas.

create or replace function public.desbloquear(pick_id text)
 returns text
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare p public.picks; precio int; saldo int; es_admin boolean;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  select * into p from public.picks where id = pick_id;
  if not found then return 'no existe'; end if;
  if p.inicio <= now() then return 'ya empezó'; end if;
  if exists (select 1 from public.desbloqueos where usuario = auth.uid() and pick = pick_id) then return 'ok'; end if;
  select monedas, admin into saldo, es_admin from public.perfiles where id = auth.uid() for update;
  precio := case when es_admin or public.es_pro() then 0 else public.precio_pick(p) end;
  if coalesce(saldo, 0) < precio then return 'sin monedas'; end if;
  update public.perfiles set monedas = monedas - precio where id = auth.uid();
  insert into public.desbloqueos (usuario, pick, monedas) values (auth.uid(), pick_id, precio);
  if precio > 0 then
    insert into public.movimientos (usuario, cantidad, motivo, pick) values (auth.uid(), -precio, 'desbloqueo', pick_id);
  end if;
  return 'ok';
end $function$;

revoke execute on function public.desbloquear(text) from public, anon;
grant execute on function public.desbloquear(text) to authenticated;
notify pgrst, 'reload schema';
