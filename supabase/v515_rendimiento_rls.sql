-- v515 — «LA BASE NO RESPONDIÓ; MOSTRAMOS EL ARCHIVO DE RESPALDO».
-- 29-oct 19:02 UTC: la consulta de picks de la página tardó 6,5 s y salió 500 (el anónimo tiene 3 s), y las de
-- picks_premium/picks_vip, 9 s. Causa: las políticas de RLS llamaban es_pro() / auth.uid() / el ajuste
-- «premium_con_cuenta» UNA VEZ POR FILA (miles por carga). Envueltas en (select …) Postgres las calcula UNA vez
-- por consulta (initPlan; es lo que recomienda Supabase). Mismas reglas, mismo resultado; sólo más rápido.
-- Y el índice que faltaba: la página filtra y ordena picks por `inicio`.

create index if not exists picks_inicio on public.picks (inicio);
create index if not exists desbloqueos_pick on public.desbloqueos (pick);

drop policy if exists "premium a quien le toca" on public.picks_premium;
create policy "premium a quien le toca" on public.picks_premium for select using (
  (select public.es_pro())
  or exists (select 1 from public.desbloqueos d where d.pick = picks_premium.id and d.usuario = (select auth.uid()))
  or exists (select 1 from public.picks p where p.id = picks_premium.id and p.estado in ('verde', 'roja', 'nula'))
  or ((select auth.uid()) is not null
      and (select exists (select 1 from public.ajustes a where a.clave = 'premium_con_cuenta' and a.valor = '1')))
);

drop policy if exists "sólo el VIP" on public.picks_vip;
create policy "sólo el VIP" on public.picks_vip for select to authenticated using ((select public.es_pro()));

drop policy if exists "la IA a quien le toca" on public.ia_analisis;
create policy "la IA a quien le toca" on public.ia_analisis for select using (
  (select public.es_pro()) or evaluado is not null
  or ((select auth.uid()) is not null
      and (select exists (select 1 from public.ajustes where clave = 'premium_con_cuenta' and valor = '1')))
);

drop policy if exists "cada quien sus desbloqueos" on public.desbloqueos;
create policy "cada quien sus desbloqueos" on public.desbloqueos for select using ((select auth.uid()) = usuario);

drop policy if exists "cada quien sus seguidos" on public.seguidos;
create policy "cada quien sus seguidos" on public.seguidos for all using ((select auth.uid()) = usuario) with check ((select auth.uid()) = usuario);

drop policy if exists "cada quien su perfil" on public.perfiles;
create policy "cada quien su perfil" on public.perfiles for all using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
