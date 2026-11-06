-- v546 — índices de claves foráneas.
-- Cambios aditivos: no alteran filas, permisos ni reglas de negocio.
-- Comparado contra el catálogo el 2026-11-04: son las 6 claves que marca el asesor; tablas de ≤ 72 kB.
--
-- Se quitó `alter function nivel_pick set search_path`: una función SQL con SET ya no se puede insertar en la
-- consulta, y historial_niveles la evalúa fila por fila. No da seguridad real: no es SECURITY DEFINER y no toca
-- tablas. El aviso function_search_path_mutable del asesor se acepta a propósito.

begin;

create index if not exists codigos_regalo_usado_por_idx
  on public.codigos_regalo (usado_por);

create index if not exists compras_usuario_idx
  on public.compras (usuario);

create index if not exists desbloqueos_combinada_combinada_idx
  on public.desbloqueos_combinada (combinada);

create index if not exists movimientos_usuario_idx
  on public.movimientos (usuario);

create index if not exists seguidos_pick_idx
  on public.seguidos (pick);

create index if not exists suscripciones_usuario_idx
  on public.suscripciones (usuario);

commit;
