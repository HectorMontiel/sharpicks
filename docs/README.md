# Documentación de arquitectura y hardening de SharPicks

Esta documentación acompaña la rama `hardening/free-audit-2026-10`. Los documentos describen el estado observado y el procedimiento objetivo; no significan que la migración o los cambios de producción ya se hayan ejecutado.

## Documentos

1. [Manual de migración 0 a 100](MANUAL_MIGRACION_SHARPICKS_0_A_100.md): arquitectura destino, preparación de repositorio privado, seguridad de Actions, migración por fases, backups, Supabase, performance, pruebas, rollback y checklist de cierre.
2. [Inventario de dependencias de los 18 workflows](INVENTARIO_DEPENDENCIAS_WORKFLOWS.md): clasificación de cada flujo, scripts, secretos observados, contratos, oleadas de extracción y gates.
3. [Clasificación de activos y modelo de amenazas](CLASIFICACION_ACTIVOS_Y_MODELO_AMENAZAS.md): código/modelos/datasets, amenazas, controles, backups y riesgos críticos.
4. [Plan de separación del core privado](PLAN_SEPARACION_CORE_PRIVADO.md): decisión de mantener el repositorio actual público, inventario inicial, flujos dependientes y criterios de aceptación.

## Estado actual

- Repositorio principal: permanece público.
- Rama de trabajo: `hardening/free-audit-2026-10`.
- PR: [#1](https://github.com/HectorMontiel/sharpicks/pull/1), draft, no fusionado.
- Repositorio privado `sharpicks-core`: pendiente de creación manual.
- Migración de código/datos: no iniciada.
- Producción/Supabase: sin cambios ejecutados por esta documentación.

## Regla

No fusionar ni desplegar basándose únicamente en documentación. Cada fase requiere sus evidencias y criterios de aceptación.
