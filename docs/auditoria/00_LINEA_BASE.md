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

- **Head remoto/local revisado:** `ac510af65aac76be66e29d8e5a104162d1744f01`; rama `hardening/free-audit-2026-10`; árbol de trabajo limpio al verificarlo.
- **PR #1:** sigue abierto y draft; `headRefOid` concuerda con `ac510af`.
- **CI remoto:** los workflows `Verificar instalación limpia de SharPicks`, `Validar SharPicks sin desplegar` y `Tests seguros SharPicks v402` reportan `queued` para `ac510af`. También permanecen en cola ejecuciones de SHAs anteriores. Ninguna se reporta como aprobada para este head.
- **Validación local posterior:** 43 tests de unittest, `test_v510.py`, `py_compile` y `git diff --check` pasaron en Python 3.12 para el árbol con código hasta `f638b2d`; los commits posteriores `c5b18ab` y `ac510af` sólo cambiaron documentación. No equivale a CI ni staging.
- **Cambios posteriores medibles:** downloader comprueba SHA-256 de metadata antes de extraer y rechaza entradas tar inseguras; para `sharpicks-core` exige `CORE_MODELS_READ_TOKEN`. Se preparó `supabase/auditoria_catalogo_readonly.sql`, pero no se ejecutó contra una base. `ADR-0001` sigue propuesta.
- **Exposición de la release:** el snapshot revisado registra 73 assets, 72 archivos `.tar.gz`, 735,067,828 bytes y digests SHA-256 para todos; ningún asset fue descargado, retirado ni reemplazado.
- **Estado de repositorio/producción:** no se pudo resolver `sharpicks-core`; no se conectó Supabase staging ni se ejecutó migración o cambio productivo.

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
