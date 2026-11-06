-- v555 — la política que le faltó a v547: mismo predicado, auth.uid() evaluado una sola vez.
-- El asesor de Supabase marca 12 políticas (auth_rls_initplan) y v547 cubre 11.
-- Sin aplicar. Comparada contra el catálogo de producción el 2026-11-04.

begin;

alter policy "cada quien sus reportes; el admin todos" on public.reportes
  using (
    (select auth.uid()) = usuario
    or exists (
      select 1 from public.perfiles f
      where f.id = (select auth.uid()) and f.admin
    )
  );

commit;
