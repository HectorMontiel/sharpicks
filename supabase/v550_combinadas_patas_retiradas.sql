-- v550 — LAS PATAS RETIRADAS DE LAS COMBINADAS DEL USUARIO. El usuario (31-oct): «en las combinadas que había metido se
-- ven patas en blanco… y una combinada de cuota arriba de 2 no muestra que ganó las monedas; eso tiene que aparecer».
-- El exportador borraba los picks que el modelo retiraba antes de empezar, también si estaban en una combinada de un
-- usuario (ya no: exportar_web._patas_fijas). Y esta liquidación sólo miraba las patas que seguían en la base: con 2 de
-- 5 borradas, la de cuota 2,14 se cerró verde con la cuota de las 3 que quedaban (1,67) y sin premio.
-- Ahora:
--   · mientras falte una pata y el partido sea reciente (< 2 días), la combinada espera;
--   · una pata que ya no existe = retirada por el modelo: no cuenta (como una nula);
--   · si faltó alguna pata, el premio se calcula con la cuota con la que el usuario armó la combinada (no fue su culpa).

create or replace function public.liquidar_combinadas_usuario() returns integer
language plpgsql security definer set search_path = public as $liquidar$
declare
  c record; v_estado text; v_cuota numeric; v_premio int; v_hechas int := 0; v_total int; v_hay int;
begin
  for c in select * from public.combinadas_usuario where estado = 'pendiente' order by creado loop
    select count(*) into v_hay from public.picks p where p.id = any (c.patas);
    if v_hay < cardinality(c.patas) and c.inicio > now() - interval '2 days' and v_hay > 0
       and exists (select 1 from public.picks p where p.id = any (c.patas) and p.estado not in ('verde', 'roja', 'nula')) then
      continue;                                   -- aún se juega lo que queda: espera
    end if;
    select case when bool_or(p.estado = 'roja') then 'roja'
                when bool_and(p.estado in ('verde', 'nula')) and bool_or(p.estado = 'verde') then 'verde'
                when bool_and(p.estado = 'nula') then 'nula'
                else 'pendiente' end,
           exp(sum(ln(case when p.estado = 'verde' then p.cuota else 1 end)))
      into v_estado, v_cuota
      from public.picks p where p.id = any (c.patas);
    if v_hay = 0 and c.inicio < now() - interval '2 days' then v_estado := 'nula'; end if;
    if v_estado is null or v_estado = 'pendiente' then continue; end if;
    if v_hay < cardinality(c.patas) then v_cuota := c.cuota; end if;      -- faltó una pata por el modelo: su cuota armada
    v_premio := 0;
    if v_estado = 'verde' and not exists (
         select 1 from public.combinadas_usuario o where o.usuario = c.usuario and o.dia = c.dia and o.premio > 0) then
      v_premio := case when v_cuota >= 5 then 5 when v_cuota >= 3 then 3 when v_cuota >= 2 then 2 else 0 end;
    end if;
    update public.combinadas_usuario set estado = v_estado, premio = v_premio where id = c.id;
    if v_premio > 0 then
      update public.perfiles set monedas = monedas + v_premio where id = c.usuario;
      insert into public.movimientos (usuario, cantidad, motivo) values (c.usuario, v_premio, 'combinada acertada');
      select count(*) into v_total from public.combinadas_usuario where usuario = c.usuario and premio > 0;
      if v_total % 5 = 0 then
        update public.perfiles set monedas = monedas + 5 where id = c.usuario;
        insert into public.movimientos (usuario, cantidad, motivo) values (c.usuario, 5, 'bono: 5 combinadas premiadas');
      end if;
    end if;
    v_hechas := v_hechas + 1;
  end loop;
  return v_hechas;
end;
$liquidar$;
revoke all on function public.liquidar_combinadas_usuario() from public, anon, authenticated;
grant execute on function public.liquidar_combinadas_usuario() to service_role;

-- las combinadas que ya se cerraron mal (verdes con patas borradas y sin premio): se vuelven a liquidar con la regla nueva
update public.combinadas_usuario c set estado = 'pendiente'
 where c.estado = 'verde' and c.premio = 0 and c.cuota >= 2 and c.creado > now() - interval '15 days'
   and exists (select 1 from unnest(c.patas) x where not exists (select 1 from public.picks p where p.id = x));
select public.liquidar_combinadas_usuario();
