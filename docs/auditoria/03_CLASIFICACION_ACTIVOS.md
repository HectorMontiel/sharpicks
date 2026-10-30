# Clasificación de activos

- **Estado:** OBSERVADO en árbol Git y metadatos de release; etiquetas por ruta implementadas como candidatas, decisión manual pendiente y ningún traslado ejecutado.
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
| Release pública `modelos-latest` | [`release_modelos_latest.json`](release_modelos_latest.json): 73 assets / 735,067,828 bytes; 72 `.tar.gz` con nombres `modelos-*`, 1 manifiesto JSON; todos reportan digest SHA-256 | Activos de modelo publicados públicamente; candidatos privados confirmados por el nombre/metadata, contenido interno no inspeccionado | Registry o release privada de `sharpicks-core`; preservar primero, migrar y validar antes de cualquier cambio | **P1 confirmado.** El publicador de esta rama exige destino privado verificado; el workflow omite staging de `modelos/` al fallar y requiere readiness para retirar modelos. La exposición histórica continúa; assets no descargados/eliminados |
| Inventario por cada blob rastreado | [`asset_inventory.json`](asset_inventory.json), snapshot del commit `cb6c3e434390101ee204addc11b68e2251f99e13`; incluye path, modo, OID Git y tamaño | 1,880 blobs / 660,235,222 bytes; candidatos heurísticos: 183 `private_candidate`, 161 `historical`, 195 `public_candidate`, 22 `generated`, 2 `shareable_contract_candidate`; etiquetas solapadas y los 1,880 requieren revisión | Debe decidirse archivo por archivo con revisión de contenido, consumidores, lineage y propietario | No lee contenido; no incluye historial Git, untracked/ignored ni assets de releases |
| Secrets | Workflows referencian nombres de secrets de servicios | Secreto | GitHub Environments/Core según mínimo privilegio | No se leyeron valores; exposición real no comprobada |
| Documentación y workflows | Reglas y operación visibles en repo público | Pública, salvo valores/estrategias sensibles | Mantener documentos generales y quitar ejemplos confidenciales | Revisar contenido antes de separar |

## Regla de migración y retención

1. Generar inventario con ruta, tamaño, SHA-256, último consumidor observado y naturaleza.
2. Preservar una copia cifrada independiente antes de cualquier movimiento.
3. Migrar a destino privado y verificar conteos, hashes, carga/lectura y un restore aislado.
4. Adaptar consumidores y comparar salida en modo sombra.
5. Retirar del árbol público sólo después de demostrar que el flujo nuevo funciona; evaluar historia, forks, release assets, cachés y artifacts como superficies independientes.

## Inventario reproducible por ruta

`tools/asset_inventory.py` usa `git ls-tree` sobre un revision seleccionado, por lo que cubre blobs rastreados aun si no están presentes en un sparse checkout. No abre ni ejecuta los archivos. El snapshot adjunto se generó desde `cb6c3e434390101ee204addc11b68e2251f99e13`. Las etiquetas `private_candidate`, `public_candidate`, `historical`, `generated`, `sensitive` y `shareable_contract_candidate` son señales de revisión, pueden solaparse y no equivalen a una decisión sobre propiedad o destino. Cada registro conserva `review_required` hasta una evaluación humana.

Para regenerar el inventario del HEAD actual:

```powershell
python tools/asset_inventory.py --output docs/auditoria/asset_inventory.json
```

El reporte generado se debe actualizar en un commit posterior al código que lo genera para que `revision` identifique el árbol analizado. La lista no cubre Git history, artifacts, assets de release, ni archivos ignorados/no rastreados; éstos requieren inventarios separados. El OID informado es el identificador Git del blob, no un checksum SHA-256 de distribución.

### Release pública de modelos

`tools/release_asset_inventory.py` obtiene únicamente metadatos mediante `gh api` y no descarga los archivos. El snapshot `release_modelos_latest.json` conserva nombre, tamaño, tipo MIME, estado, timestamps, contador de descargas y digest comunicado por GitHub; omite URLs. La API confirmó 73 assets y un total de 735,067,828 bytes, de los que 72 son archivos `modelos-*.tar.gz` y uno `modelos_publicados.json`; los 73 tienen digest `sha256:` válido. El nombre de archivo no demuestra el contenido del tar, por lo que la clasificación del payload sigue siendo candidata hasta inspección controlada.

La existencia de archivos de modelos en un release de repositorio público es una exposición confirmada respecto al objetivo de alojar modelos privados. Se registra como P1 por confidencialidad de propiedad intelectual. No se descargan, borran, reemplazan ni ocultan assets durante esta auditoría; el corte requiere migración privada reproducible, consumidores adaptados, rollback verificado y autorización para cambiar distribución.

No se deben borrar ni sobrescribir activos con base sólo en esta tabla.
