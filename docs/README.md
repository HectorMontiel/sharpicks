# Documentación de arquitectura y hardening de SharPicks

Esta documentación acompaña la rama `hardening/free-audit-2026-10`. Los documentos describen el estado observado y el procedimiento objetivo; no significan que la migración o los cambios de producción ya se hayan ejecutado.

## Documentos

1. [Manual de migración 0 a 100](MANUAL_MIGRACION_SHARPICKS_0_A_100.md): arquitectura destino, preparación de repositorio privado, seguridad de Actions, migración por fases, backups, Supabase, performance, pruebas, rollback y checklist de cierre.
2. [Inventario de dependencias de los 18 workflows](INVENTARIO_DEPENDENCIAS_WORKFLOWS.md): clasificación de cada flujo, scripts, secretos observados, contratos, oleadas de extracción y gates.
3. [Clasificación de activos y modelo de amenazas](CLASIFICACION_ACTIVOS_Y_MODELO_AMENAZAS.md): código/modelos/datasets, amenazas, controles, backups y riesgos críticos.
4. [Grafo de dependencias por entrypoint](GRAFO_DEPENDENCIAS_ENTRYPOINTS.md): imports directos, datos/archivos, variables de entorno y fronteras para extraer el core sin romper la web ni Telegram.
5. [Plan de separación del core privado](PLAN_SEPARACION_CORE_PRIVADO.md): decisión de mantener el repositorio actual público, inventario inicial, flujos dependientes y criterios de aceptación.
6. [Línea base](auditoria/00_LINEA_BASE.md): inventario medido, SHA, PR, checks, limitaciones y riesgos del corte.
7. [Grafo actual](auditoria/01_GRAFO_ARQUITECTURA.md): vista lógica parcial y límites de análisis.
8. [Auditoría de Actions](auditoria/02_AUDITORIA_GITHUB_ACTIONS.md): inventario, pins, permisos y validación pendiente.
9. [Control de ejecución](CONTROL_EJECUCION_SHARPICKS.md): tareas verificables, estados y bloqueos.
10. [Arquitectura objetivo](arquitectura/01_ARQUITECTURA_OBJETIVO.md): límites público/privado y flujo de ejecución.
11. [Contratos](arquitectura/02_CONTRATOS_PUBLICO_PRIVADO.md): contrato v1 implementado y DTOs pendientes.
12. [Distribución del core](arquitectura/03_ESTRATEGIA_DISTRIBUCION_CORE.md): alternativa seleccionada y requisito de acceso.
13. [Auditoría Supabase](auditoria/05_AUDITORIA_SUPABASE.md): evidencia local y pruebas staging pendientes.
14. [Estrategia de testing](calidad/01_ESTRATEGIA_DE_TESTING.md) y [matriz de regresión](calidad/02_MATRIZ_REGRESION.md).

## Estado actual

- Repositorio principal: permanece público.
- Rama de trabajo: `hardening/free-audit-2026-10`.
- PR: [#1](https://github.com/HectorMontiel/sharpicks/pull/1), draft, no fusionado.
- Repositorio privado `sharpicks-core`: pendiente de creación manual.
- Migración de código/datos: no iniciada.
- Producción/Supabase: sin cambios ejecutados por esta documentación.
- Acciones de GitHub: fijadas por SHA en `bae8759973b2ef8f3d5c5c4ea38e2025a0caca46`; los checks `instalar`, `tests` y `validar` aprobaron sobre ese SHA.
- Contrato público v1: implementado y 12 tests unitarios locales aprobados; el CI del SHA `f53cd2646c219516293d195a4b6ab72b4fab6c68` está en curso.

## Regla

No fusionar ni desplegar basándose únicamente en documentación. Cada fase requiere sus evidencias y criterios de aceptación.
