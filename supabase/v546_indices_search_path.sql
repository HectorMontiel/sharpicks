-- v546 — índices de claves foráneas y search_path explícito.
-- Cambios aditivos: no alteran filas, permisos ni reglas de negocio.
-- Ejecutar primero en entorno de pruebas y comparar el plan de consultas.

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

-- Función IMMUTABLE y sin SQL dinámico; fijar el path evita depender
-- del search_path mutable de la sesión que la invoque.
alter function public.nivel_pick(text, boolean, numeric, numeric)
  set search_path = pg_catalog, public;

commit;
