-- v510 — EL HISTORIAL CUENTA POR EL MISMO DÍA QUE LA PORTADA.
-- El usuario (28-oct, 23:57): «en el historial me estás dando menos acertadas que en la página principal».
-- La portada agrupa por el día del partido en hora de CDMX (`diaDe` en web/app.js: la hora de inicio), y la
-- vista agrupaba por la columna `fecha`, que en los partidos de la noche trae el día UTC (el siguiente):
--     28-oct  portada 172 ✅ 39 ❌   historial 186 ✅ 46 ❌
--     27-oct  portada 178 ✅ 32 ❌   historial 146 ✅ 22 ❌
-- Ahora la vista usa el día de CDMX de `inicio` (y `fecha` sólo si no hay hora). Mismas columnas.
create or replace view public.historial with (security_invoker = true) as
select coalesce((inicio at time zone 'America/Mexico_City')::date, fecha) as fecha,
       count(*) filter (where estado = 'verde' and coalesce(tipo, 'pick') <> 'error') as verdes,
       count(*) filter (where estado = 'roja' and coalesce(tipo, 'pick') <> 'error') as rojas,
       count(*) filter (where estado = 'verde' and elige) as verdes_elige,
       count(*) filter (where estado = 'roja' and elige) as rojas_elige,
       count(*) filter (where estado = 'verde' and tipo = 'error') as verdes_error,
       count(*) filter (where estado = 'roja' and tipo = 'error') as rojas_error,
       round(sum(case when estado = 'verde' then cuota - 1 when estado = 'roja' then -1 else 0 end) * 100, 1) as gana_por_100
  from public.picks
 group by 1
 order by 1 desc;
grant select on public.historial to anon, authenticated;
