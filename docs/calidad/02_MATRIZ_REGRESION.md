# Matriz de regresión inicial

- **Estado:** OBSERVADO; baseline predictivo aún no capturado.
- **Fecha:** 2026-10-30.

| Área | Comparación requerida | Evidencia actual | Gate de extracción |
|---|---|---|---|
| Predicción/probabilidad | evento, mercado, selección y probabilidad en fixture idéntico | No hay baseline de caracterización nuevo en esta fase | Diferencias explicadas y aprobadas antes de cambiar reglas |
| Ranking/selección | orden, picks incluidos/excluidos, razones y límites | Pendiente | Shadow run concordante dentro de tolerancia aprobada |
| Cuotas/EV | fuente, timestamp, cuota decimal, margen y EV | Pendiente | Inputs frescos y unidad explícita |
| Calibración/modelo | métricas por deporte/liga, versión de modelo/deps/features | `requirements.txt` fija algunas dependencias de pickle | Artefacto compatible y rollback ensayado |
| Web export | campos, niveles público/premium/VIP, metadatos | Tests web existentes y allowlist contractual v1 parcial | No hay campos privados ni cambio de formato no versionado |
| Telegram | contenido, segmentación, deduplicación | No se enviaron mensajes de prueba | Preview + chat aislado + clave idempotente |
| Backups | conteos, relaciones, checksums, roles tras restore | No hay restauración demostrada | Restore aislado aprobado |
| Contrato v1 | schema/tipos/hashes/status | 9 pruebas unitarias locales | CI aprobado para SHA del PR |

No se declara equivalencia predictiva hasta guardar fixtures de referencia representativos y reproducibles. Los umbrales de tolerancia los debe determinar el baseline existente, no una cifra arbitraria.
