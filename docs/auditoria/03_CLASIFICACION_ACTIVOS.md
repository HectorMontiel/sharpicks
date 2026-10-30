# Clasificación de activos

- **Estado:** OBSERVADO en árbol público y metadatos de release; decisión de traslado recomendada, no ejecutada.
- **Fecha/SHA:** 2026-10-30 / `228c86a7fb03ed555465e56971170565f3029d9b`.
- **Criterio:** clasificar por confidencialidad, sensibilidad, procedencia, posibilidad de regeneración y dependencias. El nombre o la extensión no prueba propiedad intelectual ni datos personales.

## Matriz de activos

| Activo | Evidencia observada | Clasificación | Destino recomendado | Estado/precaución |
|---|---|---|---|---|
| Motores de predicción, scoring, selección, features, calibración y reglas | 768 archivos Python en el repo; entrypoints acoplados según el grafo de 12 scripts | Propietario; código fuente | `sharpicks-core` privado, después de caracterizar comportamiento y dependencias | No movido ni eliminado |
| Modelos serializados `.joblib` | 5 en `modelos/`; `modelo_tda.joblib` mide 65,666,778 bytes | Propietario; generado y versionado | Almacenamiento/release privado con SHA-256, manifiesto de runtime y modelo | Mantener intacto hasta backup/restore y carga reproducible |
| `corners_snapshots.csv` | 104,589,619 bytes, versionado en el repo público | Histórico/posible propietario; regenerabilidad por verificar | Core/almacenamiento privado después de validar lineage y retención | No borrar; revisar historial Git y consumidores |
| `bajas_historico.csv` | 30,092,841 bytes | Histórico/posible propietario | Core privado o almacén de datos controlado | No borrar; sensibilidad/retención por confirmar |
| `historico_partidos.csv` | 5,040,036 bytes y referencia directa desde pipeline según grafo previo | Histórico de entrenamiento/operación | Core privado si contiene features/labels propietarios | Preservar y mapear dependencias |
| `team_stats*.json` | 68 archivos versionados | Caché/datos transformados; propietario/sensibilidad por verificar | Privado para datos de entrenamiento; publicar sólo resumen allowlisted | No asumir que por ser JSON es público |
| Otros CSV, JSON, snapshots, ledgers e historiales | 266 CSV/CSV.gz y 554 JSON en total | Mixto: histórico, caché, salida, configuración o fixtures | Clasificación uno por uno; datos privados al almacén privado | Pendiente de inventario detallado por path y uso |
| Payloads debajo de `web/` | Sitio estático y exportaciones mencionadas por workflows | Público si pasa allowlist; puede contener datos premium | `sharpicks` sólo con campos aprobados y pruebas de fuga | Revisar contenido y pipeline antes de publicar |
| Supabase SQL/Edge Functions | 52 archivos SQL y 10 funciones en el árbol | Código de integración y reglas de negocio; mixto | Contratos/adaptadores públicos o implementación privada según lógica | No prueba esquema/despliegue actual |
| Backup en Actions | Workflow genera ciphertext/HMAC con retención declarada de 30 días | Sensible/privado; generado | Destino privado independiente, retention policy y restore probado | No se inspeccionó artifact real ni se restauró |
| Release `modelos-latest` | 73 assets; 735,067,828 bytes combinados según GitHub API | Modelo/dataset; probable privado | Registry o release privada del core | Assets no descargados; sus nombres y contents requieren inventario |
| Secrets | Workflows referencian nombres de secrets de servicios | Secreto | GitHub Environments/Core según mínimo privilegio | No se leyeron valores; exposición real no comprobada |
| Documentación y workflows | Reglas y operación visibles en repo público | Pública, salvo valores/estrategias sensibles | Mantener documentos generales y quitar ejemplos confidenciales | Revisar contenido antes de separar |

## Regla de migración y retención

1. Generar inventario con ruta, tamaño, SHA-256, último consumidor observado y naturaleza.
2. Preservar una copia cifrada independiente antes de cualquier movimiento.
3. Migrar a destino privado y verificar conteos, hashes, carga/lectura y un restore aislado.
4. Adaptar consumidores y comparar salida en modo sombra.
5. Retirar del árbol público sólo después de demostrar que el flujo nuevo funciona; evaluar historia, forks, release assets, cachés y artifacts como superficies independientes.

No se deben borrar ni sobrescribir activos con base sólo en esta tabla.
