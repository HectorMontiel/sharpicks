-- v531 — EL MORADO DE LA IA, MEDIDO EN PÚBLICO. Los 💎/🔷/🥇 que la IA marca (confianza 5 = «mayor probabilidad»,
-- 4 = «a favor») contra los del mismo nivel sin marca. Mismo cálculo de nivel que la página. Para el historial.
create or replace function public.ia_morado_tasa() returns table (tono int, nivel text, n bigint, aciertos bigint)
language sql stable security definer set search_path = public as $$
  with p as (
    select p.partido, p.fecha, p.estado,
      case when p.elige then 'Diamante' when p.prob >= 0.85 then 'Platino' when p.prob >= 0.80 then 'Oro' else 'Plata' end as nivel
    from public.picks p
    where p.estado in ('verde', 'roja') and coalesce(p.tipo, '') not in ('error', 'analisis'))
  select case when a.confianza >= 5 then 2 when a.confianza >= 4 then 1 else 0 end, p.nivel,
    count(*), count(*) filter (where p.estado = 'verde')
  from p join public.ia_analisis a on a.partido = p.partido and a.fecha = p.fecha
  where a.confianza is not null and p.nivel in ('Diamante', 'Platino', 'Oro')
  group by 1, 2
$$;
revoke all on function public.ia_morado_tasa() from public;
grant execute on function public.ia_morado_tasa() to anon, authenticated;
