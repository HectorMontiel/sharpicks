-- v543 — LA HUELLA DE LO PÚBLICO. El vigilante (v542) midió ~350 MB de salida al día con 5 usuarios: cada pestaña
-- abierta bajaba TODOS los picks (~170 KB comprimidos por página) y las combinadas cada 3 minutos aunque nada hubiera
-- cambiado (y aunque estuviera en segundo plano). Ahora la página pide primero esta huella (unos bytes) y sólo vuelve a
-- bajar picks o combinadas si su huella cambió. La huella es el md5 de cada fila completa: cualquier cambio (cuota,
-- estado, resultado, una fila nueva o borrada) la mueve.

create or replace function public.huella_publica(p_desde date, p_desde_comb date)
 returns jsonb
 language sql
 stable
 set search_path to 'public'
as $function$
  select jsonb_build_object(
    'picks', (select md5(coalesce(string_agg(md5(p::text), '' order by p.id), '')) || ':' || count(*) from public.picks p where p.fecha >= p_desde),
    'comb', (select md5(coalesce(string_agg(md5(c::text), '' order by c.id), '')) || ':' || count(*) from public.combinadas c where c.fecha >= p_desde_comb)
  )
$function$;

revoke all on function public.huella_publica(date, date) from public;
grant execute on function public.huella_publica(date, date) to anon, authenticated;
notify pgrst, 'reload schema';
