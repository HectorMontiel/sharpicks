# Auditoría estática de Supabase

- **Estado:** OBSERVADO por revisión de archivos; estado remoto y de producción BLOQUEADO por falta de proyecto conectado.
- **Fecha/SHA:** 2026-10-30 / `228c86a7fb03ed555465e56971170565f3029d9b`.
- **Alcance:** migraciones SQL y configuración/Edge Functions versionadas. No se ejecutaron migraciones ni se consultó la base de datos.

## Evidencia local

- El árbol contiene 52 archivos SQL, `supabase/config.toml` y 10 carpetas/funciones de Edge en el commit observado.
- `config.toml` contiene una única asignación explícita `verify_jwt = false`, para `functions.comentario`. La función valida origen/método, verifica una sesión real con `auth.getUser()` si recibe un token de usuario, permite comentarios anónimos y usa un RPC con service role. Esto confirma lógica de validación en código, no el config desplegado ni una auditoría de rate limit bajo carga.
- `stripe-webhook` valida `Stripe-Signature` con HMAC y timestamp antes de procesar el evento, y consulta el objeto a Stripe. No se probó con eventos reales.
- `mp-webhook` consulta el pago/suscripción con el token del proveedor antes de aplicar cambios, pero no se observa verificación local de una firma de notificación. Hace falta confirmar el protocolo de Mercado Pago habilitado en el panel y validar replay/idempotencia en staging; esto no prueba una vulnerabilidad explotable.
- Hay vistas con `security_invoker=true` (por ejemplo `historial_deportes`, `historial_niveles` en una revisión anterior, `historial`, `calibracion_picks` y `ia_medicion` tras v508), y otras con `security_invoker=false` explícito o sin opción en el SQL mostrado. Las últimas operan con privilegios del dueño según el comportamiento de PostgreSQL; sus grants, definición final y contenido requieren inspección de catálogo y pruebas por rol.
- Migraciones contienen muchas funciones `SECURITY DEFINER`, varias con `search_path` fijado. Los grants/revokes varían por función; el nombre de la función no basta para decidir si su acceso es indebido. Deben verificarse definición efectiva, propietario, ACL y contexto de identidad.
- `v508_seguridad.sql` crea `codigos_intentos`, habilita RLS, no define policy para esa tabla y revoca acceso de `anon`/`authenticated`, concediendo acceso a `service_role`. Esto es una decisión explícita en SQL, no evidencia del estado aplicado.
- `v546_indices_search_path.sql` agrega seis índices y ajusta `search_path` de `public.nivel_pick`; es transaccional. `v547_optimizacion_rls.sql` modifica 11 políticas mediante `ALTER POLICY` envolviendo `auth.uid()` como initplan y sin cambiar deliberadamente los predicados. No fueron ejecutadas ni comparadas en staging.

## Revisión de hallazgos históricos

| Hallazgo previo | Resultado de revisión local | Estado real |
|---|---|---|
| 13 tablas con RLS habilitado y sin policies | No se puede confirmar contando migraciones históricas; migraciones posteriores pueden añadir policies y el catálogo desplegado es la fuente efectiva | PENDIENTE: consultar catálogo en staging |
| 5 vistas `SECURITY DEFINER` | Hay varias definiciones que usan invoker false o el default; no se determinó el conjunto activo ni sus ACL finales | PENDIENTE: listar `pg_views`, reloptions, owner y grants |
| Funciones `SECURITY DEFINER` ejecutables por anon/authenticated | Se encuentran grants explícitos a esos roles para varias funciones; hay casos intencionales (por ejemplo acceso a agregados/funciones de negocio) y otros requieren revisar identidad/datos devueltos | PENDIENTE: auditoría por firma, cuerpo y rol |
| 10 Edge Functions con `verify_jwt=false` | Sólo hay una asignación falsa explícita en el config versionado; el resto usa el default salvo que GitHub tree/version desplegada difiera | OBSERVADO localmente; verificar config desplegada |
| Webhook Mercado Pago | Consulta estado autoritativo con API, sin verificación local de firma visible en fuente | PENDIENTE confirmar panel/protocolo y hacer prueba aislada |
| Tabla `codigos_intentos` | SQL habilita RLS, sin policy, revoca roles cliente y concede service role | OBSERVADO en v508; pendiente estado efectivo |
| Migraciones v546/v547 | SQL presente en rama, con transacción; no aplicada | PENDIENTE staging |

## No comprobado

- RLS habilitado final, policies existentes/roles cubiertos, grants/revokes, ownership, ACL de vistas y funciones, exposición por PostgREST, columnas sensibles y datos reales.
- Configuración de JWT desplegada, secretos Edge, validación de firmas de Mercado Pago, logs y rate limit.
- Índices ya existentes, costo de v546, planes de consulta, rendimiento y equivalencia funcional de v547.
- Backups Supabase, restauración, extensiones, triggers, webhooks internos, retención y políticas del proyecto.

## Plan seguro de staging

1. Obtener schema-only y catálogo del proyecto de staging con acceso de mínimo privilegio; no volcar valores sensibles.
2. Enumerar tablas públicas expuestas, RLS, policies y grants por `anon`, `authenticated` y `service_role`.
3. Enumerar vistas, opciones `security_invoker`, propietario/grants y funciones `SECURITY DEFINER` con cuerpo, `search_path` y ACL.
4. Probar cada endpoint con anon, sesión propia, sesión ajena y service role en fixtures sintéticos.
5. Aplicar v546/v547 primero en staging, comparar `EXPLAIN`, latencia, resultados y permisos; preparar rollback SQL antes de cualquier ventana productiva.
6. Validar webhooks con eventos de prueba del proveedor y repetición de la misma notificación.
7. Mantener todas las migraciones sin aplicar a producción hasta autorización explícita y evidencia de aceptación.
