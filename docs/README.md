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
15. [Grafo AST completo y datos por módulo](auditoria/python_dependency_graph.json), generado por [`tools/python_dependency_graph.py`](../tools/python_dependency_graph.py); registra imports locales, ciclos candidatos, entrypoints, llamadas dinámicas, referencias de archivos y variables de entorno.
16. [Inventario por ruta de los blobs rastreados](auditoria/asset_inventory.json), generado por [`tools/asset_inventory.py`](../tools/asset_inventory.py) desde metadatos Git; todas las clasificaciones son candidatas y requieren revisión.
17. [Snapshot de metadata del release público de modelos](auditoria/release_modelos_latest.json), sin descargas; verifica nombres, tamaños y digests de los 73 assets.
18. [Distribución del core](arquitectura/03_ESTRATEGIA_DISTRIBUCION_CORE.md): alternativa de paquete privado y gates implementados para rechazar publicación pública/no verificada.
19. [ADR-0001 de distribución del core](decisiones/ADR-0001-distribucion-core-privado.md): checkout privado fijado a SHA como propuesta; integración y aceptación pendientes.

## Estado actual

- Repositorio principal: permanece público.
- Rama de trabajo: `hardening/free-audit-2026-10`.
- PR: [#1](https://github.com/HectorMontiel/sharpicks/pull/1), draft, no fusionado.
- Repositorio privado `sharpicks-core`: pendiente de creación manual.
- Migración de código/datos: no iniciada.
- Producción/Supabase: sin cambios ejecutados por esta documentación.
- Acciones de GitHub: fijadas por SHA en `bae8759973b2ef8f3d5c5c4ea38e2025a0caca46`; los checks `instalar`, `tests` y `validar` aprobaron sobre ese SHA.
- Contrato público v1: implementado y 12 tests unitarios locales aprobados; `instalar`, `tests` y `validar` aprobaron en CI para el SHA `c162c7587cb960149459d41ede09097990250046`.
- Grafo recursivo: generado para 773 archivos Python desde `4c1223a635ed628798e547645209cba67582f65b`; batería local del analizador/contratos pasa.
- Inventario por ruta: 1,880 blobs rastreados (660,235,222 bytes) desde el tree `cb6c3e434390101ee204addc11b68e2251f99e13`; las etiquetas son heurísticas y requieren revisión humana, sin lectura de contenido.
- Release pública: snapshot de `modelos-latest` confirma 72 archivos de modelos `.tar.gz` y un manifiesto JSON (735,067,828 bytes); se registra exposición P1 y se preservan los assets mientras no exista una migración validada.
- Publicador: en esta rama requiere un destino privado explícito/verificado y no versiona ni retira modelos si falla o no se marca readiness de consumidores. CI del código `bebbe57` está en cola; integración con repo/secret real no probada.
- Descarga de modelos: verifica SHA-256 contra metadata API y valida tipos/rutas del tar antes de extraer; 9 pruebas con fixtures locales, sin descargar modelos reales. Para `sharpicks-core` exige `CORE_MODELS_READ_TOKEN` y no envía el token de Actions del repo público. CI sigue en cola.
- Lectura del core: ningún workflow productivo fue apuntado al repo privado porque aún no se ha verificado. La readiness de corte queda deliberadamente sin habilitar.
- Supabase: preparada consulta de catálogo read-only para staging y tres guardas estáticas; no hay CLI/`psql` ni conexión al proyecto aquí, por lo que la sintaxis/resultados no se declaran validados contra la instancia.
- ADR de distribución: registrada como propuesta (no operativa) la descarga del paquete privado por SHA en un job protegido; falta validar paquete y consumidores.

## Regla

No fusionar ni desplegar basándose únicamente en documentación. Cada fase requiere sus evidencias y criterios de aceptación.
