# Línea base de SharPicks

- **Fecha de auditoría:** 2026-10-30
- **Estado:** OBSERVADO; inventario reproducible del árbol y metadatos del remoto.
- **Repositorio:** `HectorMontiel/sharpicks` (público confirmado).
- **Rama local/remota:** `hardening/free-audit-2026-10` / `origin/hardening/free-audit-2026-10`.
- **Commit auditado:** `228c86a7fb03ed555465e56971170565f3029d9b` (`docs: add dependency graph to documentation index`).
- **Árbol de trabajo al iniciar:** limpio.
- **Pull request:** #1, abierto, draft, base `main`, head `hardening/free-audit-2026-10`.
- **Checks de PR consultados:** `instalar`, `tests` y `validar` aprobados en el SHA consultado.
- **Repositorio privado `sharpicks-core`:** no resoluble por la cuenta conectada; la API no permite distinguir entre inexistente y falta de acceso.

## Actualización de estado: 2026-10-30

- **Head remoto/local revisado:** `4711a16ce3103d195314987b2e5726592d1a2091`; rama `hardening/free-audit-2026-10`; árbol de trabajo limpio al verificarlo.
- **PR #1:** sigue abierto y draft; `headRefOid` concuerda con `4711a16`.
- **CI remoto:** los tres workflows (`Verificar instalación limpia de SharPicks`, `Validar SharPicks sin desplegar`, `Tests seguros SharPicks v402`) reportan `queued` para `4711a16`. En `0ab0fe0`, `validar` e instalación limpia terminaron en `success`, mientras tests seguros seguían `in_progress`; en `52b819f`, validar seguía `in_progress`. Ninguno acredita el head actual.
- **Validación local posterior:** 46 tests de unittest, 6 pruebas de `test_exportador_web_v402.py`, `test_v510.py`, `py_compile`, ausencia de lecturas de `.text` en los dos exportadores y `git diff --check` pasaron en Python 3.12 para el árbol con código hasta `4711a16`. No equivale a CI ni staging.
- **Cambios posteriores medibles:** downloader comprueba SHA-256 de metadata antes de extraer y rechaza entradas tar inseguras; para `sharpicks-core` exige `CORE_MODELS_READ_TOKEN`. Se preparó `supabase/auditoria_catalogo_readonly.sql`, pero no se ejecutó contra una base. `ADR-0001` sigue propuesta.
- **Exposición de la release:** el snapshot revisado registra 73 assets, 72 archivos `.tar.gz`, 735,067,828 bytes y digests SHA-256 para todos; ningún asset fue descargado, retirado ni reemplazado.
- **Estado de repositorio/producción:** no se pudo resolver `sharpicks-core`; no se conectó Supabase staging ni se ejecutó migración o cambio productivo.
- **Escaneo preliminar de secretos:** `tools/secret_scan.py` inspeccionó 1,040 archivos locales de 1,889 rutas versionadas (checkout sparse). Reportó dos patrones de token de prueba en `tests/test_python_dependency_graph.py:59-60`; revisión con salida redactada confirmó que son literales sintéticos de fixture. La coincidencia de `access_token` en `supabase/functions/entrar/index.ts` quedó eliminada al corregir el detector de asignaciones para ignorar referencias de código. El scan no expuso valores, excluye binarios y no inspeccionó historia; no es un escaneo de secretos completo.
- **Secret Scanning de GitHub:** habilitado en el repositorio público y confirmado por la API (`security_and_analysis.secret_scanning.status=enabled`). La API de alertas no devolvió alertas al consultar; no se considera prueba de backfill completo porque el endpoint de scan-history devuelve 404 al estar GitHub Advanced Security desactivado.


## Actualización adicional: 2026-10-30

- **Head de código:** `43273e6e971be0763480b0a92d20dbaa2a2df391`; rama autorizada; PR #1 continúa abierto y draft.
- **Cambio:** `respaldo_base.py` ya no incorpora cuerpos HTTP de Supabase a excepciones de descarga de páginas, RPC de auth o restauración. Tres pruebas canario cubren esos caminos.
- **Validación local:** 49 pruebas de `unittest discover -s tests -p "test_*.py"` y 6 pruebas del exportador pasaron en Python 3.12. También pasó `py_compile` y `git diff --check`. El escáner heurístico inspeccionó 1,041 archivos hidratados y señaló únicamente dos fixtures sintéticos ya revisados; no escanea historia ni blobs sparse.
- **CI de `43273e6`:** al corte, instalación limpia y validar estaban `in_progress`; tests seguros estaba `pending`. Ningún resultado remoto final se atribuye a este SHA todavía.
- **Límites:** la prueba es local y con mocks. No acredita backup/restore real, staging, ni seguridad del catálogo remoto.


## Actualización: DTO público web

- **Head de código:** `048143c6a1af2b25f2a180bdb17d30e68efc33ba`; PR #1 sigue abierto y draft.
- **Cambio:** `sharpicks_contracts/web_v1.py` aplica allowlist versionada v1 a `hoy.json` y `analisis.json`, preserva el sobre legado y filtra claves superiores no declaradas, datos `jug`, `ctx.lin` y claves de contexto/estadística no públicas; valida tipos, probabilidades finitas en [0,1], tipos booleanos y timestamps UTC. El exportador usa el DTO al escribir estos archivos.
- **Validación local:** 52 pruebas unittest, 6 pruebas de exportador, las pruebas heredadas seleccionadas (v383, v389, v390, v394-v396, v400 y v510), test JavaScript `test_web_v402.cjs`, compilación Python y `git diff --check` pasaron. Algunas pruebas de bots informaron que PIL no está instalado en este entorno y continuaron sin su subcaso de generación de ticket.
- **CI:** para `2f43a94`, los tres workflows terminaron `success`. En `71e0141`, `validar` e instalación limpia fueron `success`; tests seguros quedó cancelado al entrar el siguiente commit. Para los SHA `2d73980` y `048143c`, los tres workflows terminaron `success`.
- **Compatibilidad y límites:** se mantiene `picks`/`analisis` y se agrega `contract_version`; no se ha comprobado el sitio publicado/Cloudflare. Las tablas de Supabase y otros productos no pasan por este DTO.


## Actualización: recuperación de artifacts cifrados

- **Implementado localmente:** `tools/restore_backup_artifact.py` verifica el sidecar HMAC antes de iniciar OpenSSL, descifra el formato actual sin escribir un tar plano temporal, extrae sólo archivos regulares bajo `respaldo/` a un directorio nuevo y preserva el artifact fuente.
- **Pruebas locales:** la suite ahora descubre 56 tests; 55 pasan y el test de cifrado/descifrado OpenSSL se omite porque OpenSSL no está instalado localmente. Los tests de HMAC incorrecto, traversal y symlink pasan. No se usó un artifact real ni hubo conexión Supabase.
- **Validación externa:** CI de `c3141d5` aprobó los tres workflows; su runner Ubuntu ejecutó el round-trip OpenSSL con datos sintéticos. La restauración de un artifact real y una base aislada requiere staging y credenciales administradas fuera de esta tarea.
- **Runbook:** [`runbooks/restore_backup_artifact.md`](../runbooks/restore_backup_artifact.md) describe la extracción local y sus límites.
## Metodología

1. Se verificaron rama, commit y árbol con Git; el checkout usa clonación superficial y parcial (`blob:none`) porque el árbol tiene más de 650 MB. Se materializaron los fuentes Python, documentación, workflows, pruebas y SQL necesarios para inspección local. El inventario de conteos y tamaños proviene de la API GitHub del árbol recursivo del SHA, no de una descarga de todos los blobs.
2. Se consultaron metadatos de repositorio, PR #1, checks y releases mediante GitHub CLI con la sesión ya iniciada. No se leyeron ni imprimieron valores de secretos.
3. Se leyeron los documentos previos en `docs/`, el inventario de workflows y archivos de hardening de Supabase incluidos en esta rama.
4. Los hallazgos describen el árbol versionado y metadatos visibles; no prueban configuración privada, ejecución productiva, acceso real a bases de datos ni despliegues.

## Inventario medido

| Tipo | Cantidad |
|---|---:|
| Archivos versionados | 1,860 |
| Python | 768 |
| Workflows en `.github/workflows/` | 18 |
| SQL | 52 |
| JSON | 554 |
| CSV / CSV comprimido | 266 |
| Modelos `.joblib` | 5 |
| `team_stats*.json` | 68 |
| Archivos mayores de 1 MiB | 59 |
| Tamaño lógico total del árbol | 656,419,555 bytes |

Workflows observados: `claves_supabase.yml`, `cuotas_mx.yml`, `precalcular_rosters.yml`, `precalculo_dia.yml`, `radar_diario.yml`, `recalibrar.yml`, `relevo.yml`, `respaldo_base.yml`, `retrain_leagues.yml`, `sitio_web.yml`, `smoke_sharpicks.yml`, `telegram_bot.yml`, `telegram_dia_completo.yml`, `test_instalacion_limpia.yml`, `test_sharpicks_v402.yml`, `validate_sharpicks.yml`, `vigia_limites.yml` y `web_rapido.yml`.

## Activos de alto tamaño confirmados

| Ruta | Tamaño versionado | Clasificación inicial |
|---|---:|---|
| `corners_snapshots.csv` | 104,589,619 bytes | OBSERVADO; datos históricos/snapshots; revisar propiedad y sensibilidad antes de migrar |
| `modelos/modelo_tda.joblib` | 65,666,778 bytes | OBSERVADO; artefacto de modelo propietario; debe quedar privado tras migración verificada |
| `bajas_historico.csv` | 30,092,841 bytes | OBSERVADO; histórico potencialmente propietario |
| `historico_partidos.csv` | 5,040,036 bytes | OBSERVADO; histórico de entrenamiento/operación |

Los otros modelos `.joblib` son `modelos/escalador.joblib`, `modelos/mat_mundial.joblib`, `modelos/reg_goles_local.joblib` y `modelos/reg_goles_visit.joblib`. Se mantienen sin cambios mientras no exista repositorio privado accesible, respaldo comprobado y migración reproducible.

La release visible `modelos-latest` contiene 73 assets, con 735,067,828 bytes combinados según sus metadatos. No se descargaron ni se inspeccionaron los contenidos de esos assets.

## Estado de documentación y ejecución

- Ya existían `docs/README.md`, el manual de migración, inventario de workflows, clasificación preliminar de activos y grafo estático de 12 entrypoints. Su texto distingue correctamente diseño de migración ejecutada.
- La documentación previa no estaba bajo la estructura normalizada `docs/auditoria/`, y no existía el control de ejecución solicitado.
- No existe en el árbol observado una integración operativa con `sharpicks-core`; no se han movido código ni activos.
- El PR documenta que v546/v547 están pendientes de staging; esta inspección no encontró evidencia de ejecución en una base de datos.
- No se validó staging ni producción. Los checks de PR sólo acreditan sus jobs concretos sobre el SHA consultado.

## Entorno y limitaciones

- **Git/GitHub:** Git y `gh` disponibles; `gh auth status` confirmó una sesión existente sin exponer el token.
- **Checkout:** clonación superficial/parcial; el contenido no seleccionado y el historial completo no se descargaron. La auditoría de tamaño se hizo con metadatos del árbol remoto.
- **Herramientas no encontradas en PATH:** `gitleaks`, `trufflehog`, `supabase` y `pytest`. Esto no significa que no existan en otros runners.
- **No comprobado:** escaneo de secretos de todo el historial, settings de Actions y protección de ramas, configuración de secretos, ejecuciones históricas completas, contenido/retención de artifacts, grants y policies efectivos de Supabase, Edge Functions desplegadas, backups restaurables, conectividad a proveedores, producción.
- **Pruebas locales:** no ejecutadas en esta línea base. La evidencia de CI es la indicada arriba; no se atribuye como validación local.

## Evidencia reproducible

Comandos y consultas usados: `git status --short --branch`, `git log -1 --format=...`, `git ls-tree -r --name-only HEAD`, `gh repo view`, `gh pr view 1`, `gh pr checks 1` y consultas GitHub REST a `/git/trees/<sha>?recursive=1` y `/releases`.

## Riesgos priorizados

- **P1 — propiedad intelectual y datos accesibles públicamente:** el árbol público incluye modelos entrenados, scoring y grandes históricos; la release pública incluye 73 assets. No se retiraron archivos ni se reescribió historial porque el destino privado no es accesible y la preservación/migración no está verificada.
- **P1 — exposición histórica no evaluada:** todavía no hay evidencia de escaneo de secretos del historial completo ni inventario de cachés/artifacts históricos.
- **P1 — seguridad/recuperación Supabase sin validación externa:** las migraciones están en archivos, pero sus efectos reales no pueden inferirse sin staging.

## Próxima revisión

La sección inicial conserva la línea base inmutable del SHA `228c86a`; la actualización superior registra el estado actual observado en `ac510af`. Actualizar el estado después de cada cambio relevante y separar evidencia local, CI, staging y producción.
