# Control de ejecución de SharPicks

- **Corte:** 2026-10-30, base auditada `228c86a7fb03ed555465e56971170565f3029d9b`; último commit remoto `f53cd2646c219516293d195a4b6ab72b4fab6c68`.
- **Rama:** `hardening/free-audit-2026-10`.
- **PR:** #1, abierto y draft.
- **Regla de progreso:** no se calcula porcentaje hasta definir y cerrar un conjunto finito de criterios verificables; el inventario inicial contiene trabajo aún no dimensionado.

Estados permitidos: PENDIENTE, EN EJECUCIÓN, IMPLEMENTADO, EN VALIDACIÓN, VALIDADO, BLOQUEADO, REQUIERE AUTORIZACIÓN, DESCARTADO CON JUSTIFICACIÓN.

| ID | Fase | Tarea verificable | Dependencias | Estado | Archivos/área | Pruebas/evidencia | Bloqueo |
|---|---|---|---|---|---|---|---|
| F0-01 | 0 | Confirmar repo, rama, commit, árbol limpio, PR y checks | Ninguna | VALIDADO | Git, PR #1 | SHA y checks actuales registrados en `docs/auditoria/00_LINEA_BASE.md` | Ninguno |
| F0-02 | 0 | Repetir conteos de archivos, workflows, SQL, JSON, CSV, modelos y releases | F0-01 | VALIDADO | Árbol remoto y releases | GitHub REST: 1,860 archivos, 768 Python, 18 workflows, 52 SQL, 554 JSON, 266 CSV, 5 JOBLIB; release de 73 assets | Metadatos; no incluye contenido de todos los blobs |
| F0-03 | 0 | Crear inventario reproducible de entorno, limitaciones y riesgos iniciales | F0-01 | IMPLEMENTADO | `docs/auditoria/00_LINEA_BASE.md` | Evidencia documentada; revisión pendiente en este commit | Ninguno |
| F1-01 | 1 | Completar grafo estático y clasificación de módulos Python | F0-02 | EN EJECUCIÓN | Fuentes Python, documentación de grafo | Documento anterior cubre imports directos de 12 entrypoints, no los 768 módulos | Imports dinámicos y resolución transitiva |
| F1-02 | 1 | Confirmar archivos/variables/side effects de entrypoints críticos | F1-01 | PENDIENTE | Entry points descritos en mandato | Pendiente | Ninguno |
| F2-01 | 2 | Inventariar triggers, permisos, Actions, artifacts y secretos referenciados de 18 workflows | F0-02 | IMPLEMENTADO | `.github/workflows/`, `docs/auditoria/02_AUDITORIA_GITHUB_ACTIONS.md` | Fuente: 18 YAML; referencias y triggers inspeccionados | Config privada y settings no visibles |
| F2-02 | 2 | Fijar Actions externas a SHA y ejecutar regresión CI | F2-01 | VALIDADO | 16 workflows con `uses:`; 2 sin Actions externas | Commit `bae8759`; `instalar`, `tests`, `validar` aprobados | No incluye reducción de permisos |
| F2-03 | 2 | Reducir permisos por job tras validar cada escritura | F2-01 | PENDIENTE | `.github/workflows/` | No se alteran cron ni permisos todavía | Configurar/regresión de flujos que escriben |
| F3-01 | 3 | Clasificar todos los activos y destino con evidencia | F0-02 | EN EJECUCIÓN | Código, modelos, datos, releases, `docs/auditoria/03_CLASIFICACION_ACTIVOS.md` | Conteos/sizes y activos principales registrados | Falta clasificación individual de históricos y 73 assets |
| F3-02 | 3 | Ejecutar escaneo histórico de secretos sin imprimir valores | F0-01 | PENDIENTE | Historial completo, releases, artifacts | Herramientas dedicadas no encontradas; historial aún superficial | Requiere recuperar/clonar historia completa y revisar artifacts |
| F4-01 | 4 | Crear arquitectura objetivo y ADR de distribución | F1-01, F3-01 | PENDIENTE | `docs/arquitectura/`, `docs/decisiones/` | Diseño previo existe en `docs/PLAN_SEPARACION_CORE_PRIVADO.md` | Ninguno |
| F4-02 | 4 | Implementar y versionar contrato de ejecución público v1 con DTOs/validadores | F4-01 | IMPLEMENTADO | `sharpicks_contracts/v1.py`, tests, docs arquitectura | 12 tests unitarios locales aprobados; CI del SHA `f53cd26` en curso | Falta extender DTOs dominio |
| F4-03 | 4 | Implementar integración real con core privado | Repositorio/contrato disponibles | BLOQUEADO | Workflows y adaptadores | No se observó `sharpicks-core` ni acceso a él | La API no resuelve el repo; no pedir tokens por chat |
| F5-01 | 5 | Extraer componente propietario incremental con caracterización y rollback | F4-03, F6-01 | BLOQUEADO | Código core y consumidores | No se movió código en esta fase | Repositorio core no disponible y baseline de regresión incompleta |
| F6-01 | 6 | Versionar modelos/datasets, checksums, manifiestos y recuperación privada | F4-03 | BLOQUEADO | Modelos, datos, release | Inventario visible; no se migraron activos | Repositorio/almacenamiento privado no disponible |
| F7-01 | 7 | Desacoplar exportador web y Telegram mediante salidas allowlisted | F4-02 | PENDIENTE | `exportar_web.py`, bots, contratos | Pendiente |
| F8-01 | 8 | Revisar SQL, vistas, funciones, RLS y Edge Functions en archivos | F0-02 | EN EJECUCIÓN | `supabase/`, `docs/auditoria/05_AUDITORIA_SUPABASE.md` | Revisión estática de config, funciones/vistas y v546/v547 | No prueba estado desplegado ni catálogo completo |
| F8-02 | 8 | Ejecutar pruebas de seguridad de Supabase en staging y preparar rollback | F8-01 | REQUIERE AUTORIZACIÓN | Proyecto de staging | No ejecutado | Acceso/entorno staging y autorización externa |
| F9-01 | 9 | Probar restauración aislada de backup cifrado | Datos/entorno aislado | REQUIERE AUTORIZACIÓN | `respaldo_base.py`, workflow, staging | CI existente no constituye restore | Proyecto/credenciales aislados |
| F10-01 | 10 | Añadir pruebas de contrato, integración y regresión | F4-02, F5-01 | EN EJECUCIÓN | `tests/`, `docs/calidad/` | 12 tests de contrato locales pasan; CI del SHA `f53cd26` en curso | Baseline de predicción aún no caracterizado |
| F10-02 | 10 | Capturar baseline predictivo determinista por deporte/mercado | Datos sintéticos/fixtures y motores actuales | PENDIENTE | Fixtures/regresión | Pendiente | Se requiere seleccionar fixtures sin exponer datos propietarios |
| F11-01 | 11 | Medir y optimizar carga/costo tras baseline real | F0-02, workflows | PENDIENTE | Workflows críticos | Duraciones de checks de PR observadas; no equivalen a costos | Datos de facturación no visibles |
| F12-01 | 12 | Implementar logs/alertas/runbooks y validar privacidad | Arquitectura y servicios | PENDIENTE | Operación y entrypoints | Pendiente |
| F13-01 | 13 | Mantener manual, ADRs, runbooks y criterios alineados a lo implementado | Todas | EN EJECUCIÓN | `docs/` | Índice/documentación previos existen | Continua |
| GIT-01 | 23 | Mantener rama autorizada, PR draft, cambios pequeños y evidencia | Trabajo local | EN EJECUCIÓN | Rama y PR #1 | Rama correcta; commits `bae8759`, `6c74576`, `601e52a`, `40e65e4` y `f53cd26` están en PR; sigue draft; checks de `f53cd26` en curso | Ninguno para este bloque |

## Distinción de validación

- **Analizado/documentado:** evidencia registrada, sin cambio funcional.
- **Implementado:** el código/configuración está en la rama, aún sin prueba suficiente.
- **Validado localmente:** comando ejecutado en este checkout.
- **Validado en CI:** check sobre un SHA identificado.
- **Validado en staging/producción:** requiere evidencia del entorno indicado; no inferirlo de tests con mocks ni de CI.

## Bloqueos externos concretos

1. `sharpicks-core` no es resoluble para la cuenta conectada; crear o conceder acceso desde GitHub es una tarea del propietario. Mientras tanto, se puede implementar el contrato público, auditar workflows y conservar los activos públicos intactos.
2. Supabase staging no está conectado a este entorno; archivos SQL no equivalen a migraciones aplicadas.
3. No hay evidencia local de restore aislado ni de configuración real de secrets/protecciones de Actions.

## Evidencia de este corte

La línea base se encuentra en [`auditoria/00_LINEA_BASE.md`](auditoria/00_LINEA_BASE.md). La lista refleja tareas verificables y evita convertir el volumen de documentación existente en progreso de implementación.
