-- v552 — MIS COMBINADAS: NI REPETIDAS NI SIN REMEDIO. El usuario (31-oct): «si ya metiste una combinada igual, que no
-- puedas volver a meter otra igual… y si te equivocaste, que se pueda eliminar».
--   · crear_combinada rechaza la misma combinada (los mismos picks, en cualquier orden) si ya la tienes;
--   · borrar_combinada la quita mientras NINGUNO de sus partidos haya empezado (después no: no se juega con el premio).
--     Se marca «borrada» (no se pierde el registro y sigue contando en el tope de 10 por día).

alter table public.combinadas_usuario drop constraint if exists combinadas_usuario_estado_check;
alter table public.combinadas_usuario add constraint combinadas_usuario_estado_check
  check (estado = any (array['pendiente', 'verde', 'roja', 'nula', 'borrada']));

create or replace function public.crear_combinada(p_patas text[])
 returns uuid
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_usuario uuid := auth.uid();
  v_n int := coalesce(array_length(p_patas, 1), 0);
  v_ok int; v_partidos int; v_cuota numeric; v_inicio timestamptz; v_id uuid;
begin
  if v_usuario is null then raise exception 'Inicia sesión para guardar tu combinada.'; end if;
  if v_n < 2 or v_n > 20 then raise exception 'Una combinada lleva de 2 a 20 picks.'; end if;
  if (select count(distinct x) from unnest(p_patas) x) <> v_n then raise exception 'Hay un pick repetido.'; end if;
  -- v552 — la misma combinada (los mismos picks, en cualquier orden) no se guarda dos veces
  if exists (select 1 from public.combinadas_usuario c
              where c.usuario = v_usuario and c.estado <> 'borrada'
                and (select array_agg(x order by x) from unnest(c.patas) x) = (select array_agg(x order by x) from unnest(p_patas) x)) then
    raise exception 'Ya guardaste esta misma combinada.';
  end if;
  select count(*), count(distinct lower(p.partido)), exp(sum(ln(p.cuota))), min(p.inicio)
    into v_ok, v_partidos, v_cuota, v_inicio
    from public.picks p
   where p.id = any (p_patas) and p.estado = 'pendiente' and p.cuota > 1
     and p.inicio > now() + interval '1 minute'
     and coalesce(p.tipo, 'pick') not in ('analisis', 'combinada')
     and (not coalesce(p.premium, false) or public.es_pro()
          or exists (select 1 from public.desbloqueos d where d.pick = p.id and d.usuario = v_usuario));
  if v_ok <> v_n then raise exception 'Algún pick ya empezó, no existe o no lo tienes desbloqueado.'; end if;
  if v_partidos <> v_n then raise exception 'Cada pick tiene que ser de un partido distinto.'; end if;
  if (select count(*) from public.combinadas_usuario c where c.usuario = v_usuario and c.creado > now() - interval '1 day') >= 10 then
    raise exception 'Llevas 10 combinadas hoy: vuelve mañana.';
  end if;
  insert into public.combinadas_usuario (usuario, patas, cuota, inicio, dia)
  values (v_usuario, p_patas, round(v_cuota, 3), v_inicio, (v_inicio at time zone 'America/Mexico_City')::date)
  returning id into v_id;
  return v_id;
end;
$function$;

create or replace function public.borrar_combinada(p_id uuid)
 returns text
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare c public.combinadas_usuario;
begin
  if auth.uid() is null then return 'inicia sesión'; end if;
  select * into c from public.combinadas_usuario where id = p_id and usuario = auth.uid() for update;
  if not found then return 'no existe'; end if;
  if c.estado <> 'pendiente' then return 'ya terminó'; end if;
  if c.inicio <= now() or exists (select 1 from public.picks p where p.id = any (c.patas) and p.inicio <= now()) then
    return 'ya empezó';
  end if;
  update public.combinadas_usuario set estado = 'borrada' where id = p_id;
  return 'ok';
end;
$function$;
revoke all on function public.borrar_combinada(uuid) from public, anon;
grant execute on function public.borrar_combinada(uuid) to authenticated;
notify pgrst, 'reload schema';
