-- v540 — «ARMA TU COMBINADA» PARA EL GRATIS CON CUALQUIER NIVEL. El usuario: «si el usuario general quiere meter
-- diferentes niveles, que se pueda, pero para desbloquear la combinada tendrá que pagar monedas de acuerdo a la cuota,
-- como están los planes». Cada pata de pago cuesta lo mismo que desbloquearla suelta (precio_pick, por su cuota) y
-- queda como un desbloqueo normal: si esa pata sale roja o nula, sus monedas regresan (devolver_si_falla).
-- Todo o nada: si no alcanzan las monedas o un partido ya empezó, no se cobra ninguna.

create or replace function public.desbloquear_varios(p_ids text[])
 returns text
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare v_id text; p public.picks; total int := 0; saldo int; r text; gratis boolean;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  if p_ids is null or cardinality(p_ids) = 0 or cardinality(p_ids) > 20 then return 'no existe'; end if;
  select monedas, coalesce(admin, false) or public.es_pro() into saldo, gratis from public.perfiles where id = auth.uid() for update;
  foreach v_id in array (select array_agg(distinct x) from unnest(p_ids) x) loop
    select * into p from public.picks where id = v_id;
    if not found then return 'no existe'; end if;
    if p.inicio <= now() then return 'ya empezó'; end if;
    if coalesce(p.premium, false) and not gratis
       and not exists (select 1 from public.desbloqueos where usuario = auth.uid() and pick = v_id) then
      total := total + public.precio_pick(p);
    end if;
  end loop;
  if coalesce(saldo, 0) < total then return 'sin monedas'; end if;
  foreach v_id in array (select array_agg(distinct x) from unnest(p_ids) x) loop
    select * into p from public.picks where id = v_id;
    if coalesce(p.premium, false) then
      r := public.desbloquear(v_id);
      if r <> 'ok' then raise exception 'desbloquear_varios: % → %', v_id, r; end if;
    end if;
  end loop;
  return 'ok';
end $function$;

revoke all on function public.desbloquear_varios(text[]) from public, anon;
grant execute on function public.desbloquear_varios(text[]) to authenticated;
notify pgrst, 'reload schema';
