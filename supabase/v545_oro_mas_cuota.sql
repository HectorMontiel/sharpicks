-- v545 — EL ORO: MÁS CUOTA, MENOS PROBABILIDAD. El usuario (30-oct): «el oro ahora se convierte en cuotas más altas pero
-- con menor probabilidad, por eso lo bajamos al 70 %… para hacer notar que el diamante es muy útil y que conviene subir».
-- Medido en los picks de los últimos 30 días (70-79 % y cuota ≥ 1,25): 289 picks, ~16 por día, acierto 75,1 % a cuota
-- media 1,27. Los niveles quedan así (un solo lugar: `nivel_pick`, igual que web/app.js, exportar_web, telegram_canales
-- y combinadas_web):
--   Cuota alta (errores) · 💎 Diamante (⭐ elige) · 🔷 Platino ≥ 80 % · 🥇 Oro 70-79 % con cuota ≥ 1,25 · 🥈 Plata el resto.
-- El Oro sigue siendo lo gratis; lo de 80-84 % (antes Oro) pasa a 🔷 Platino, de pago.

create or replace function public.nivel_pick(p_tipo text, p_elige boolean, p_prob numeric, p_cuota numeric)
 returns text
 language sql
 immutable
as $function$
  select case
    when p_tipo = 'error' then 'Cuota alta'
    when coalesce(p_elige, false) then 'Diamante'
    when coalesce(p_prob, 0) >= 0.80 then 'Platino'
    when coalesce(p_prob, 0) >= 0.70 and coalesce(p_cuota, 0) >= 1.25 then 'Oro'
    else 'Plata'
  end
$function$;
grant execute on function public.nivel_pick(text, boolean, numeric, numeric) to anon, authenticated, service_role;

-- el precio: 🥇 Oro gratis (y los picks de análisis); lo demás por su cuota
create or replace function public.precio_pick(p picks)
 returns integer
 language sql
 stable
 set search_path to 'public'
as $function$
  select case
    when coalesce((p).tipo, 'pick') = 'analisis' then 0
    when public.nivel_pick((p).tipo, (p).elige, (p).prob, (p).cuota) = 'Oro' then 0
    else coalesce((
      select pc.monedas from public.precios_cuota pc
       where coalesce((p).cuota, 1) >= pc.desde and coalesce((p).cuota, 1) < pc.hasta
       order by pc.desde limit 1
    ), 10)
  end;
$function$;

create or replace view public.historial_niveles as
  select public.nivel_pick(tipo, elige, prob, cuota) as nivel,
    (count(*) filter (where estado = 'verde'))::integer as verdes,
    (count(*) filter (where estado = 'roja'))::integer as rojas,
    min(fecha) as desde,
    max(fecha) as hasta,
    round(((sum(case when estado = 'verde' then cuota - 1 when estado = 'roja' then -1::numeric else 0::numeric end) * 100)
      / nullif(count(*) filter (where estado in ('verde', 'roja')), 0)::numeric), 1) as gana_por_100
  from public.picks
  where fecha >= current_date - 30 and coalesce(tipo, 'pick') <> 'analisis'
  group by 1;

create or replace function public.ia_morado_tasa()
 returns table(tono integer, nivel text, n bigint, aciertos bigint)
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  with p as (
    select p.partido, p.fecha, p.estado, public.nivel_pick(p.tipo, p.elige, p.prob, p.cuota) as nivel
    from public.picks p
    where p.estado in ('verde', 'roja') and coalesce(p.tipo, '') not in ('error', 'analisis'))
  select case when a.confianza >= 5 then 2 when a.confianza >= 4 then 1 else 0 end, p.nivel,
    count(*), count(*) filter (where p.estado = 'verde')
  from p join public.ia_analisis a on a.partido = p.partido and a.fecha = p.fecha
  where a.confianza is not null and p.nivel in ('Diamante', 'Platino', 'Oro')
  group by 1, 2
$function$;

notify pgrst, 'reload schema';
