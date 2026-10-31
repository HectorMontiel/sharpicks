# Plan de separación: orquestador público y motor privado

**Estado:** diseño previo a ejecución. Este documento no mueve código, no cambia secretos, no modifica la visibilidad del repositorio y no despliega nada.

## Decisión de arquitectura

Mantener `HectorMontiel/sharpicks` público como repositorio de interfaz/orquestación y crear un repositorio privado independiente `sharpicks-core` para el motor propietario, modelos entrenados, históricos extensos y lógica de selección. Cloudflare Pages seguirá conectado al repositorio público para publicar únicamente `web/` y sus recursos públicos.

La separación todavía **no está implementada**: el código Python y los datos identificados continúan en el repositorio público. No interpretar este plan como protección ya conseguida.

## Inventario observado

El repositorio público contiene aproximadamente 768 archivos Python y datos/modelos de tamaño considerable. Ejemplos de activos que no deben permanecer en el repositorio público una vez validada la migración:

- `modelos/modelo_tda.joblib` y otros artefactos de `modelos/`.
- `corners_snapshots.csv`, `bajas_historico.csv`, `historico_partidos.csv` y otros históricos/ledgers.
- `team_stats*.json`, snapshots de cuotas, capturas de mercado y datos de entrenamiento.
- Motores y módulos de predicción/reentrenamiento, por ejemplo `league_engine.py`, módulos `engines/`, `train_tda_model.py`, `feature_engineering.py`, `update_team_stats.py` y módulos de calibración/riesgo.

La lista es representativa, no una lista exhaustiva de archivos que deban moverse sin revisar dependencias.

## Workflows que hoy dependen del checkout del código

Los flujos de cálculo y actualización que requieren una revisión de dependencias incluyen:

- `cuotas_mx.yml`: cuotas, barridos y capturas.
- `precalculo_dia.yml`: históricos, estadísticas, lesiones, líneas y precálculo.
- `recalibrar.yml` y `retrain_leagues.yml`: históricos, calibración y entrenamiento.
- `radar_diario.yml`: entrenamiento/medición del radar.
- `telegram_bot.yml` y `telegram_dia_completo.yml`: pipeline y publicación.
- `respaldo_base.yml`: extracción y respaldo de datos.
- `sitio_web.yml`: exportación de datos públicos y publicación de la web.
- `relevo.yml`: programación encadenada de cuotas.

No conviene reemplazar todos los checkouts por un checkout privado de golpe: algunos flujos solo necesitan datos públicos o scripts ligeros y otros sí requieren el motor privado.

## Diseño objetivo

1. **Repositorio público (orquestador/UI):** `web/`, validaciones que no revelen lógica propietaria, contratos JSON públicos, documentación operativa no sensible y workflows mínimos.
2. **Repositorio privado (core):** motores Python, entrenamiento, modelos, históricos, snapshots y utilidades internas. Sin publicar artefactos privados en releases, logs o artifacts de Actions.
3. **Interfaz entre ambos:** cada workflow obtiene el core en un directorio separado, en un SHA/tag fijado; ejecuta un entrypoint explícito y exporta únicamente resultados públicos previamente filtrados.
4. **Autenticación entre repos:** token fine-grained de solo lectura, limitado al repositorio privado y a Contents; almacenado como GitHub Actions secret. Nunca incluirlo en código, argumentos visibles, logs o artifacts.
5. **Confianza de workflows:** no entregar el token a ejecuciones de forks ni a workflows disparados por eventos no confiables; preferir `workflow_dispatch`, `schedule` y eventos controlados. Fijar acciones externas a SHA revisado.
6. **Cloudflare Pages:** mantener la integración con el repositorio público. El build recibe solo los JSON/HTML/CSS/JS públicos; nunca se copia el core ni los modelos al directorio `web/`.
7. **Costos:** antes de migrar cargas pesadas, medir minutos facturables reales por job y verificar la cuota del plan de GitHub. La duración total de workflows no equivale a minutos facturables: jobs paralelos, matrices y cancelaciones cambian el cálculo.

## Secuencia segura de migración

### Fase 0 — Preparación
- Crear manualmente el repositorio privado `sharpicks-core` desde GitHub (la integración disponible no ofrece una operación de creación de repositorios).
- Configurarlo privado, sin Pages ni publicación automática de releases.
- Configurar secret de Actions con token fine-grained read-only; no compartir el token por chat.
- Confirmar que el plan/cupo de Actions soporta la carga prevista.

### Fase 1 — Extracción sin cortar producción
- Mover primero el motor y los datos a core privado conservando un commit de referencia.
- Añadir un contrato de ejecución/versionado y una prueba de importación.
- Probar en workflow manual/no productivo: checkout de ambos repos, instalación, carga de modelo, predicción de muestra y comparación determinista de salida.
- No subir archivos del core a artifacts, caches compartidos, logs o commits públicos.

### Fase 2 — Migración workflow por workflow
- Empezar por un workflow de reentrenamiento manual y no crítico.
- Continuar con recalibración y precálculo, después cuotas/radar y finalmente Telegram.
- Mantener cada workflow en el repositorio público como orquestador, pero delegar la lógica al entrypoint privado.
- Validar outputs y métricas contra el flujo actual antes de cambiar el siguiente workflow.

### Fase 3 — Limpieza del repositorio público
- Solo después de demostrar que todos los workflows operan desde core privado, retirar del repositorio público los módulos/modelos/históricos ya migrados.
- Revisar releases, artifacts y cachés antiguos por separado; borrar solo tras verificar respaldos y retención.
- Recordar que borrar archivos en un commit nuevo no elimina su presencia del historial Git. Para purgar historial se requiere una reescritura coordinada y revisión de forks/clones.
- Ejecutar escaneo de secretos de historial completo y rotar cualquier credencial que haya estado expuesta.

## Criterios de aceptación

- [ ] El repositorio principal sigue público y Cloudflare Pages continúa conectado.
- [ ] Los workflows públicos no contienen lógica propietaria ni datasets/modelos privados.
- [ ] El token solo puede leer el repositorio privado y no aparece en logs.
- [ ] Una ejecución manual reproduce predicciones de referencia con el mismo SHA del core.
- [ ] Los workflows programados críticos pasan en secuencia, sin duplicar ejecuciones ni publicar datos privados.
- [ ] El backup privado se descifra y restaura en un entorno aislado antes de retirar artifacts antiguos.
- [ ] La cuota/costo real de Actions queda medido con uso de jobs, no con wall-clock agregado.

## Límites de este cambio

Este documento es únicamente el plan de migración. No crea el repositorio privado, no configura secretos, no mueve archivos, no altera cron, no cambia la visibilidad del repositorio actual y no despliega producción.
