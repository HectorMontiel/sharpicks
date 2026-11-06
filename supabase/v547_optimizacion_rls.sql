-- v547 — optimización de políticas RLS.
-- Mantiene exactamente los mismos predicados de propiedad; evalúa auth.uid()
-- como initplan para evitar repetirlo por fila.

begin;

alter policy "cada quien sus compras" on public.compras
  using ((select auth.uid()) = usuario);

alter policy "cada quien sus movimientos" on public.movimientos
  using ((select auth.uid()) = usuario);

alter policy "cada quien sus combinadas" on public.desbloqueos_combinada
  using ((select auth.uid()) = usuario);

alter policy "cada quien sus combinadas propias" on public.combinadas_usuario
  using ((select auth.uid()) = usuario);

alter policy "cada quien sus calificaciones" on public.ia_calificaciones
  using ((select auth.uid()) = usuario)
  with check ((select auth.uid()) = usuario);

alter policy "cada quien sus pulsos" on public.pulso_desbloqueos
  using ((select auth.uid()) = usuario);

alter policy "cada quien sus suscripciones" on public.suscripciones
  using ((select auth.uid()) = usuario);

alter policy "users_select_own_transactions" on finanzas.transacciones
  using ((select auth.uid()) = user_id);

alter policy "users_select_own_tokens" on finanzas.token_vault
  using ((select auth.uid()) = user_id);

alter policy "users_select_own_audit_log" on finanzas.vault_access_log
  using ((select auth.uid()) = user_id);

alter policy "own_aliases" on finanzas.card_aliases
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

commit;
