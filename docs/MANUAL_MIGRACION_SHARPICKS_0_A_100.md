# Manual maestro de migración SharPicks: de 0 a 100

**Versión:** 1.0 · **Estado:** preparación documentada; ejecución bloqueada hasta disponer del repositorio privado y sus secretos.
**Objetivo:** separar el motor propietario y los datos de SharPicks del repositorio público sin interrumpir las automatizaciones, la web, Supabase ni Telegram.

> Este manual es el procedimiento operativo. No implica que el core ya se haya movido. Hasta completar las pruebas, el repositorio público sigue conteniendo código y datos que deben considerarse expuestos.

## 0. Principios que no se negocian

1. No convertir el repositorio principal en privado como parte de esta migración.
2. No desplegar producción ni cambiar cron/horarios mientras se valida cada fase.
3. No copiar secretos, históricos privados, modelos o código propietario al repositorio público.
4. No publicar artifacts, caches, logs, releases ni outputs que contengan el core privado.
5. No usar tokens personales amplios. Usar GitHub fine-grained PAT con acceso **Contents: read-only** únicamente a `sharpicks-core`.
6. No entregar ese token a workflows de forks, pull requests externos o eventos no confiables.
7. No migrar todos los workflows de una sola vez. Un flujo por fase, con comparación y rollback.
8. No eliminar respaldos existentes hasta verificar un respaldo alternativo, descifrado y restauración completa.
9. No fusionar ni desplegar cambios de base de datos sin validar columnas, funciones, políticas y plan de ejecución en un entorno aislado.
10. Toda predicción publicada debe conservar procedencia, versión de motor, fecha de datos y estado de frescura.

## 1. Estado inicial y alcance

### 1.1 Repositorios

- Público actual: `HectorMontiel/sharpicks` (se conserva público).
- Privado objetivo: `HectorMontiel/sharpicks-core` (debe crearse manualmente desde GitHub; la integración disponible no ofrece creación de repositorios).
- Rama de preparación: `hardening/free-audit-2026-10`.
- PR de preparación: [#1](https://github.com/HectorMontiel/sharpicks/pull/1), draft; no fusionar hasta cerrar las puertas de validación.

### 1.2 Componentes de SharPicks

| Dominio | Ejemplos detectados | Destino |
|---|---|---|
| Web pública | `web/`, HTML/CSS/JS y JSON deliberadamente público | Público |
| Exportador público | `exportar_web.py` y contrato de salida, tras revisión de que no filtre lógica/datos | Público temporal; reducir a exportador mínimo |
| Motor fútbol | `league_engine.py`, `train_tda_model.py`, `feature_engineering.py`, `update_team_stats.py` | Privado |
| Motores por deporte | `engines/` (MLB, tenis, NBA, KBO, etc.) | Privado |
| Modelos | `modelos/**/*.joblib`, calibradores y pesos | Privado |
| Históricos | `historico_*.csv`, `*_historico.csv`, ledgers, snapshots y capturas | Privado |
| Estado intermedio | `team_stats*.json`, snapshots de cuotas, lesiones, alineaciones y señales | Privado salvo subconjunto público filtrado |
| Integración | contratos JSON, validadores de esquema, dispatchers y workflows | Público sin lógica propietaria |
| Credenciales | Supabase service role, Telegram, proveedores de cuotas, Mercado Pago/Stripe, Cloudflare | GitHub/Supabase secrets; nunca Git |

La lista es una clasificación inicial basada en nombres y usos observados, no autorización para mover indiscriminadamente cada archivo. Cada archivo debe pasar por el inventario de dependencias y clasificación de datos.

## 2. Arquitectura objetivo

```text
GitHub Actions (repo público sharpicks)
  ├─ valida evento, inputs y permisos
  ├─ checkout del orquestador (SHA del workflow)
  ├─ checkout de sharpicks-core (SHA/tag inmutable, directorio separado)
  ├─ instala dependencias bloqueadas
  ├─ ejecuta entrypoint versionado del core
  ├─ valida esquema, frescura y límites del resultado
  └─ publica SOLO datos aprobados
       ├─ Supabase (API/RPC con credencial mínima)
       ├─ commit de JSON público filtrado, si aplica
       ├─ Telegram (solo flujo de notificación)
       └─ Cloudflare Pages (solo web/ y assets públicos)

Repositorio privado sharpicks-core
  ├─ engines/
  ├─ models/
  ├─ training/
  ├─ ingestion/
  ├─ historical_data/
  ├─ calibration/
  ├─ tests/
  └─ interfaces/ (schemas/contratos)
```

El core no debe escribir directamente en `web/` ni en el checkout público. Devuelve un artefacto de salida con esquema definido; el orquestador valida y filtra antes de publicarlo.

### 2.1 Contrato de ejecución

Definir entrypoints estables por dominio, por ejemplo:

- `python -m sharpicks_core.cli cuotas --dias 2`
- `python -m sharpicks_core.cli precalculo --fecha YYYY-MM-DD`
- `python -m sharpicks_core.cli retrain --deportes ...`
- `python -m sharpicks_core.cli calibrate --corte YYYY-MM-DD`
- `python -m sharpicks_core.cli export-public --output /tmp/sharpicks-public`

Son nombres objetivo, no comandos existentes. Implementarlos dentro del core y probarlos antes de actualizar workflows.

Cada ejecución debe registrar:
- `core_version` (SHA completo o tag firmado/inmutable).
- `schema_version` de salida.
- `run_id`, `generated_at_utc`, `data_as_of`.
- deporte, liga, mercado y universo de eventos cubiertos.
- fuentes utilizadas y estado (real, fallback, estimado).
- conteos de filas/partidos/selecciones y checksum.
- warnings y errores; no incluir tokens, headers ni datos personales.

## 3. Preparación del repositorio privado (fase manual)

1. En GitHub, crear un repositorio nuevo llamado `sharpicks-core`.
2. Elegir **Private** desde el inicio; no crear primero como público.
3. No activar Pages, releases automáticos ni publicación de paquetes.
4. Añadir solo al propietario y colaboradores estrictamente necesarios.
5. Configurar branch protection para `main`: PR obligatorio, checks requeridos y sin force-push.
6. Crear un fine-grained PAT con:
   - Resource owner: cuenta propietaria.
   - Repository access: solo `sharpicks-core`.
   - Repository permissions: `Contents: Read-only`.
   - Sin Administration, Actions write, Secrets, Workflows write ni permisos de escritura.
   - Expiración definida y procedimiento de renovación.
7. En el repo público, guardar el token como Actions secret `SHARPICKS_CORE_READ_TOKEN`.
8. Guardar también un pin `SHARPICKS_CORE_REF` como variable o input protegido con SHA completo; nunca usar `main` en producción.
9. No pegar el token en ChatGPT, issues, commits, comandos, logs o artifacts.
10. Verificar que la política de Actions permite que los workflows confiables lean el secret.

**Bloqueo:** no avanzar a la fase de checkout privado hasta que el repositorio y el secret existan. No pedir ni recibir el token por chat.

## 4. Inventario archivo por archivo y matriz de workflows

### 4.1 Workflows identificados

| Workflow | Función observada | Dependencias / salida | Orden de migración |
|---|---|---|---|
| `cuotas_mx.yml` | Cuotas MX, barrido capa 1, anclas | `cuotas_mx.py`, `barrido_capa1.py`, `anclas.py`; snapshots y JSON | Alta, después de piloto |
| `precalculo_dia.yml` | Ingesta y precálculo multideporte | históricos, FotMob/ESPN, lesiones, remates, líneas, pronóstico | Alta |
| `retrain_leagues.yml` | Reentrenamiento diario multiliga/deporte | `league_engine.py`, `engines/*`, modelos, históricos, snapshots | Alta, después de reproducibilidad |
| `recalibrar.yml` | Históricos, calibración, backtesting y riesgo | `recalibrar_todo.py`, calibradores, ledgers, reportes | Alta |
| `radar_diario.yml` | Modelo de errores/radar | `radar_errores.py`, pick ledger y capturas | Media |
| `precalcular_rosters.yml` | Plantillas y goleadores ESPN | `espn_extras.py`, caché goleadores | Media |
| `telegram_bot.yml` | Pipeline y bot diario | `pipeline_total.py`, `bot_telegram.py` | Media |
| `telegram_dia_completo.yml` | Pipeline y distribución multideporte | `pipeline_total.py`, `bot_dia_completo.py` | Media |
| `sitio_web.yml` | Pruebas, exportación, pulso, canales, Cloudflare | `exportar_web.py`, `combinadas_web.py`, JSON web | Mantener delgado; no requiere core en cada etapa si consume datos aprobados |
| `web_rapido.yml` | Deploy frontend estático | `web/`, Wrangler | Público, no mover |
| `relevo.yml` | Encadenar cuotas | `cuotas_mx.yml` | Público, no mover |
| `respaldo_base.yml` | Backup cifrado Supabase | `respaldo_base.py`, clave de backup | Separar destino y restauración; no incluir core |
| `vigia_limites.yml` | Monitoreo de cuotas/uso | `vigia_limites.py` | Público mínimo o función segura |
| `claves_supabase.yml` | Operación manual de claves/config | revisar contenido y permisos | No dar acceso al token core salvo necesidad |
| `smoke_sharpicks.yml` | Smoke tests | endpoints/contratos públicos | Público |
| `test_instalacion_limpia.yml` | Bootstrap DB y tests | SQL/migrations de prueba | Público sin fixtures privados |
| `test_sharpicks_v402.yml` | Regresión | tests web/export | Público |
| `validate_sharpicks.yml` | Validación ligera | lint/tests | Público; nunca descargar core para PRs externos |

### 4.2 Matriz de dependencias por flujo

Antes de modificar un workflow, generar una lista exacta de imports/archivos usados por cada entrypoint. La matriz anterior es nivel workflow; no sustituye el grafo de imports.

Para cada script:
1. Buscar imports locales estáticos y dinámicos.
2. Seguir imports recursivamente hasta librerías externas.
3. Detectar lecturas/escrituras de CSV, JSON, joblib, pickle, SQLite y carpetas.
4. Detectar llamadas a Supabase, Telegram, casas de apuestas, APIs externas y Git.
5. Marcar secretos y permisos requeridos por operación.
6. Etiquetar archivo: `public`, `private-code`, `private-data`, `secret`, `public-output`.
7. Registrar propietario, workflow consumidor, tamaño, sensibilidad, frecuencia y criticidad.
8. Bloquear migración si el grafo contiene dependencias sin clasificar.

## 5. Migración paso a paso

### Fase A — Baseline reproducible
- Congelar una referencia de `main` y una referencia de core candidata.
- Seleccionar 10–20 eventos de prueba representativos por deporte/mercado.
- Guardar resultados de referencia anonimizados y checksums.
- Registrar versiones Python, SO, dependencias y fuentes.
- Confirmar que el mismo input y el mismo core SHA producen la misma salida dentro de tolerancias definidas.
- No usar eventos futuros para entrenar/evaluar ni introducir leakage temporal.

**Aceptación:** baseline versionado y reproducible, sin exponer datos sensibles.

### Fase B — Extracción del core
- Crear estructura de paquetes con `pyproject.toml` y módulos con nombres estables.
- Mover lógica por dominio, no mediante un volcado masivo sin pruebas.
- Separar datos de entrenamiento de código fuente.
- Añadir manifiesto de modelos: SHA-256, tamaño, framework, versión Python, features, fecha de entrenamiento, dataset fingerprint y métricas de validación.
- Sustituir rutas relativas implícitas por rutas configurables.
- Añadir validación de integridad antes de cargar joblib/pickle.
- Mantener compatibilidad de CLI hasta que todos los workflows migren.
- No copiar historiales completos a artifacts ni al repo público.

**Aceptación:** instalación limpia del core y tests de importación/carga de modelo pasan en entorno privado.

### Fase C — Primer workflow piloto
Elegir `retrain_leagues.yml` manual con inputs controlados o un job aislado de validación; no empezar por el ciclo de cuotas productivo.

- Checkout público en SHA fijado.
- Checkout privado en `$RUNNER_TEMP/sharpicks-core` usando token read-only.
- Validar que el checkout privado corresponde exactamente al SHA esperado.
- Instalar dependencias desde lockfile/cache privado seguro.
- Ejecutar el CLI privado en modo dry-run.
- Comparar resultados con baseline.
- Verificar que logs/artifacts no contienen rutas, código, datos o secretos del core.
- No hacer push a `main`, no publicar Telegram, no tocar Supabase ni Cloudflare en el piloto.

**Aceptación:** salida equivalente, logs limpios, token no expuesto y ningún side effect externo.

### Fase D — Delegación de publicación
- El core produce outputs en directorio temporal.
- Orquestador valida JSON contra JSON Schema.
- Rechazar NaN/Infinity, fechas inválidas, cuotas/probabilidades fuera de dominio, duplicados y resultados incompletos.
- Aplicar allowlist de campos públicos.
- Publicar solo datasets necesarios para web/Supabase.
- Firmar/manifiestar output con SHA de core, esquema y checksum.
- No publicar predicciones no verificadas o fallback como datos reales.
- Separar outputs de auditoría interna y outputs públicos.

**Aceptación:** test de contrato, filtrado y no exposición de columnas privadas.

### Fase E — Migración progresiva
Orden recomendado:
1. Piloto manual de reentrenamiento.
2. Recalibración/backtesting.
3. Pre-cálculo diario.
4. Cuotas MX y radar.
5. Roster/plantillas.
6. Telegram.
7. Exportador web solo si una dependencia privada lo requiere.

Para cada flujo:
- PR independiente.
- Mantener workflow previo disponible para rollback.
- Habilitar ejecución manual primero.
- Ejecutar dos ciclos comparativos en paralelo sin duplicar publicación.
- Comparar conteos, frescura, cobertura, cuotas, métricas y checksum.
- Activar cron nuevo solo tras aprobación de los criterios.
- Evitar que dos workflows escriban simultáneamente el mismo JSON/CSV/branch.
- Usar concurrency groups y locks con expiración para operaciones exclusivas.
- Retirar dependencia antigua únicamente tras 3 ejecuciones programadas exitosas.

### Fase F — Limpieza pública
Solo cuando todos los consumidores migraron:
- Eliminar del árbol público código/modelos/históricos ya alojados y probados en privado.
- Revisar cada workflow para asegurar que ya no importe esos archivos del checkout público.
- Retirar releases/assets y artifacts expuestos únicamente después de tener respaldo privado verificado.
- Auditar caches y logs.
- Evaluar purga del historial Git con `git filter-repo` o herramienta equivalente, en ventana coordinada; la eliminación en HEAD no borra commits antiguos.
- Documentar forks/clones que puedan retener contenido.
- Ejecutar secret scanning de historial completo y rotar credenciales si hay exposición.

### Fase G — Estabilización
- Observar al menos 7 días de ejecuciones.
- Revisar fallos, duración por job, minutos facturables, concurrencia y costos.
- Verificar que los horarios y encadenamientos de relevo no se duplican ni quedan colgados.
- Confirmar Cloudflare Pages sigue publicando desde el repositorio público.
- Confirmar bot, Supabase y datos web reciben los mismos contratos.
- Cerrar el plan solo después de restauración probada y rollback ensayado.

## 6. Implementación segura en GitHub Actions

Patrón de referencia para un job confiable (adaptar y probar; no copiar a producción sin revisar el evento y permisos):

```yaml
permissions:
  contents: read

jobs:
  core:
    if: github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout del orquestador
        uses: actions/checkout@<SHA_REVISADO>
        with:
          persist-credentials: false

      - name: Checkout del core privado
        uses: actions/checkout@<SHA_REVISADO>
        with:
          repository: HectorMontiel/sharpicks-core
          ref: ${{ vars.SHARPICKS_CORE_REF }}
          token: ${{ secrets.SHARPICKS_CORE_READ_TOKEN }}
          path: .private/sharpicks-core
          persist-credentials: false

      - name: Validar referencia y ejecutar
        env:
          CORE_REF: ${{ vars.SHARPICKS_CORE_REF }}
        run: |
          test -d .private/sharpicks-core
          test "$(git -C .private/sharpicks-core rev-parse HEAD)" = "$CORE_REF"
          # Instalar y ejecutar el CLI tras definir el contrato.
```

Advertencias:
- `<SHA_REVISADO>` es placeholder; no usar tags flotantes en producción.
- El filtro `if` no es suficiente para cualquier evento; revisar `pull_request_target`, `workflow_run`, dispatches encadenados y permisos heredados.
- No ejecutar código de PR externo con el token disponible.
- No imprimir `env`, `secrets`, URLs con credenciales ni comandos con tokens.
- No persistir credenciales de checkout.
- No cachear el directorio privado en cache accesible por workflows públicos.
- Evitar upload-artifact del checkout privado; si se necesita un modelo temporal, cifrarlo y limitar acceso/retención con diseño separado.

## 7. Secretos y permisos

### 7.1 Inventario (nombres orientativos; confirmar nombres reales en repo)
- `SHARPICKS_CORE_READ_TOKEN`: Actions secret del orquestador, Contents read-only en core.
- Supabase: URL pública y anon key en frontend; service role solo server-side/Actions de confianza.
- Telegram bot token y chat IDs.
- API keys de proveedores de cuotas/estadísticas.
- Mercado Pago/Stripe secrets en Edge Function secrets.
- `RESPALDO_CLAVE` solo en contexto de backup y restauración.
- Cloudflare API token restringido al proyecto Pages y permisos de deploy necesarios.

### 7.2 Controles
- Rotación con fecha, dueño y procedimiento de revocación.
- No reutilizar PAT para Supabase, Cloudflare ni servicios externos.
- Secret masking no es garantía si el secreto se transforma; nunca imprimirlo.
- Limitar permisos de workflow por job, no usar `permissions: write-all`.
- Usar environment approvals para jobs que publiquen o modifiquen estado.
- Secretos de producción ausentes en PRs y tests de forks.
- Revisar permisos de `GITHUB_TOKEN`; usar read-only por defecto.

## 8. Datos, privacidad y publicación

Clasificar cada campo antes de exportarlo:
- Público: evento, equipos, mercado, cuota y pick que el producto decide mostrar.
- Interno: métricas de calibración, edge interno, ranking de modelo, datos de proveedores bajo licencia.
- Privado usuario: identificadores, compras, suscripciones, movimientos, tokens, historiales de usuario.
- Secreto: API keys, credenciales, firmas, tokens.
- Modelo/propiedad intelectual: pesos, features, parámetros, datasets propietarios.

Reglas:
- Nunca incluir información de usuario en JSON público, artifacts o logs.
- No subir dumps Supabase al repositorio público.
- No mezclar esquema `finanzas` con datos públicos.
- Verificar licencias y términos de proveedores antes de almacenar/republicar datos.
- Retención y eliminación definidas para snapshots y artifacts.
- Los backups deben tener destino privado, autenticación, cifrado autenticado moderno (preferir AES-GCM o age sobre CBC+HMAC nuevo diseño), checksum, versionado y prueba de restauración.
- Guardar la clave fuera del mismo almacenamiento que el backup.
- Probar restauración de datos y Auth en un proyecto aislado; documentar limitaciones de identities/password hashes.

## 9. Backup y recuperación ante desastres

### Procedimiento mínimo
1. Crear backup completo con inventario de schemas, tablas, vistas, funciones, roles, grants, policies, Storage metadata y Auth según posibilidad.
2. Exportar datos con paginación y conteos por tabla.
3. Crear manifiesto con fecha UTC, versión del script, schema version, conteos, bytes y hashes.
4. Cifrar antes de transferir/almacenar.
5. Subir a almacenamiento privado independiente del repositorio público.
6. Verificar HMAC/AEAD y checksum después de descargar.
7. Restaurar en proyecto de staging aislado.
8. Validar integridad referencial, filas, usuarios, funciones, policies, Storage y login de prueba.
9. Medir RPO/RTO y documentar pasos manuales.
10. Mantener al menos una copia fuera de la cuenta/proyecto principal.

### No borrar backups actuales
Los artifacts históricos del repo público se consideran potencialmente expuestos. No borrarlos hasta:
- Tener destino privado operativo.
- Tener dos backups válidos.
- Restaurar al menos uno completamente.
- Evaluar retención, acceso y necesidad legal/operativa.
Después, retirar los artifacts públicos y revisar accesos/logs. Si hubo datos personales/secretos expuestos, evaluar obligaciones y rotar credenciales.

## 10. Supabase: seguridad y cambios DB

- No mover secretos de Supabase al core ni al frontend.
- Service role solo en backend confiable.
- Revisar RLS y grants reales antes de tocar tablas sin policies.
- Las vistas SECURITY DEFINER requieren comprobar owner, grants y campos antes de cambiar a SECURITY INVOKER.
- Las funciones SECURITY DEFINER deben tener search_path fijo, validar argumentos y conceder EXECUTE mínimo.
- `verify_jwt=false` exige validar firma/secret propio o autenticación de proveedor; no es por sí solo un hallazgo explotable.
- Webhooks de pagos deben verificar firma cuando proveedor lo soporte y volver a consultar el pago con API oficial.
- v546/v547 siguen pendientes: comparar columnas/FK/function signature/policies contra el schema actual; aplicar primero en staging; revisar EXPLAIN y regresión; después preparar migración aprobada.
- No cambiar RLS de tablas sin policies sin analizar grants y uso de service role.
- No alterar producción desde esta migración de repositorios.

## 11. Performance y costos

- Separar minutos facturables de wall-clock elapsed; contabilizar por job, runner y paralelismo.
- Medir costo por workflow y por ejecución; estimar mes con cron real y reintentos.
- Evitar runners dormidos (el relevo actual usa un job que espera y dispara cuotas); evaluar un scheduler ligero solo si mantiene fiabilidad y no añade coste.
- No aumentar frecuencia de cuotas ni polling de clientes hasta medir frescura y demanda.
- Medir egress real con datos de proveedor; estimaciones desde tamaño de respuesta no son factura.
- Vigilar DB, egress cached/uncached, Edge invocations, Storage, Realtime, conexiones, CPU, RAM, p95/p99 y errores.
- Ejecutar pruebas de carga solo en staging con cuentas sintéticas; nunca estrés de producción ni pagos reales.
- Escenarios: 10/50/100/250/500 VUs, ramp, spike, soak, stress y recovery; adaptar topes al plan y detener automáticamente ante errores/latencia.

## 12. Pruebas y gates de lanzamiento

### Unitarias
- Importación de todos los paquetes.
- Carga y checksum de cada modelo.
- Contratos de salida.
- Validación de cuotas/probabilidades y ausencia de NaN.
- Filtros de datos personales y columnas privadas.
- Idempotencia de publicación.
- Locks y concurrencia.

### Integración
- Checkout privado por SHA.
- Ejecución CLI en runner limpio.
- Acceso a Supabase con permisos mínimos.
- Telegram en chat de pruebas.
- Exportador web y schema validation.
- Restore de backup en staging.

### Regresión del motor
- Fixtures versionados por deporte/liga/mercado.
- Comparación de probabilidades, rankings, EV y selección final.
- Tolerancias numéricas explícitas.
- Backtesting walk-forward sin fuga temporal.
- Comparación de cobertura y freshness.
- Cualquier cambio material en métricas bloquea el rollout hasta explicarse.

### Seguridad
- Secret scanning del historial.
- Dependabot/pinning de actions.
- SBOM y lockfile de dependencias.
- Análisis de permisos de workflows.
- Test de que PR externo no recibe token privado.
- Test de que logs/artifacts no filtran contenido privado.
- Revisión de artefactos/releases públicos.

### Criterios para pasar de fase
- Todos los tests críticos verdes.
- Dos ejecuciones manuales reproducibles.
- Tres ejecuciones programadas exitosas antes de retirar flujo antiguo.
- Cero exposición de secretos/datos privados.
- Rollback probado.
- Costos dentro del presupuesto y límites.
- RPO/RTO aceptados.

## 13. Rollback

Por cada workflow migrado:
1. Mantener el YAML anterior identificado en commit/tag.
2. Tener variable para volver al último SHA core validado.
3. Si falla import, predicción, output o publicación, detener publicación y marcar ejecución fallida.
4. Rehabilitar temporalmente el entrypoint anterior sin publicar dos veces.
5. Revertir el PR del workflow, no el histórico de datos.
6. Reconciliar outputs generados durante la ventana.
7. Registrar causa raíz y evidencia antes de reintentar.

No hacer rollback que vuelva a publicar datasets o modelos privados en el repo público.

## 14. Checklist de cierre 0–100

### Gobierno y repos
- [ ] Repositorio privado creado y protegido.
- [ ] Propietarios y colaboradores mínimos.
- [ ] Token fine-grained read-only configurado como secret.
- [ ] SHA core fijado y auditable.
- [ ] Repo público permanece público y sin lógica/datos privados tras limpieza.
- [ ] Historial Git, releases y artifacts revisados.

### Código y workflows
- [ ] Grafo de dependencias completo.
- [ ] Core empaquetado con CLI/contratos versionados.
- [ ] Piloto manual exitoso.
- [ ] Cada workflow migrado y validado individualmente.
- [ ] Concurrency/locks y escritura de outputs controlados.
- [ ] Cloudflare Pages no depende del repo privado.
- [ ] Telegram y Supabase reciben outputs validados.

### Datos y recuperación
- [ ] Modelos con manifiesto y checksum.
- [ ] Datos clasificados y privados.
- [ ] Backup privado cifrado y verificado.
- [ ] Restore completo de staging.
- [ ] RPO/RTO documentados.
- [ ] Artifacts antiguos retirados después de validación.

### Seguridad y operación
- [ ] Secret scan de historial.
- [ ] Credenciales expuestas rotadas.
- [ ] RLS, grants, funciones y webhooks auditados.
- [ ] Migraciones probadas en staging.
- [ ] Logs/artifacts sin secretos.
- [ ] Carga y costos medidos.
- [ ] Observabilidad y alertas.
- [ ] Rollback probado.
- [ ] 7 días de estabilidad observada.

**Regla de cierre:** no declarar SharPicks listo para lanzamiento mientras haya un checkbox crítico sin evidencia adjunta.

## 15. Evidencias a conservar

Por cada gate guardar:
- Commit SHA del orquestador y del core.
- Run IDs de GitHub Actions y resultado.
- Versión Python/dependencias.
- Fixtures/checksums de entrada y salida.
- Resumen de métricas de regresión.
- Logs saneados (sin datos sensibles).
- Informe de seguridad y permisos.
- Evidencia de backup y restauración.
- Costos/minutos por job.
- Decisión de rollout/rollback, responsable y fecha.

## 16. Límites y bloqueos actuales

- El repositorio privado debe crearse desde la interfaz de GitHub; el conector disponible no expone creación de repositorios.
- El token debe configurarse en GitHub Actions Secrets desde la cuenta; no se solicita ni comparte por chat.
- El grafo de dependencias archivo por archivo aún debe completarse con análisis de imports y acceso a ficheros.
- No se ha movido código ni datos al repositorio privado.
- No se han aplicado las migraciones v546/v547 a Supabase.
- No se ha ejecutado un restore integral.
- No se ha probado el Service Worker en navegador real.
- No se ha cambiado ningún cron, visibilidad, secreto o despliegue de producción en esta fase.
