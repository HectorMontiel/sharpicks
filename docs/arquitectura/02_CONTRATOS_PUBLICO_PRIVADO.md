# Contratos público/privado

- **Estado:** IMPLEMENTADO parcialmente — ejecución v1 y DTO de predicción allowlisted en `sharpicks_contracts/v1.py`; resto de contratos de dominio pendiente.
- **Fecha:** 2026-10-30.

## Contratos disponibles

| Objeto | Versión/función | Validación |
|---|---|---|
| `RunRequest` | `contract_version=1.0.0`; evento/ventana, alcance deportivo, parámetros sin campos de secreto, manifiestos y salidas solicitadas | campos desconocidos rechazados, UUID, timestamps UTC, ventana ordenada, tipos JSON y nombres de manifiesto únicos |
| `InputArtifact` | nombre lógico, versión semántica, SHA-256, tamaño y clasificación `public/private` | digest lowercase de 64 hex, tamaño entero no negativo, versión semántica |
| `PublicPrediction` | evento/deporte/liga/mercado/selección, probabilidad, cuota decimal, nivel de acceso y hora | allowlist fija, probabilidad finita en [0,1], cuota decimal > 1, nivel reconocido, UTC |
| `RunResult` | status, duración, versión/commit del core, manifiestos, predicciones allowlisted, warnings y código de error | SHA de commit completo, orden de tiempos, unknown fields rechazados; partial/failed no pueden llevar predicciones |

## Convenciones

- Serialización JSON UTF-8, compacta y con claves ordenadas.
- `contract_version` semántica; versión desconocida se rechaza.
- Timestamp ISO-8601 con timezone UTC (`Z` serializado); unidades monetarias/cuotas en decimal odds y probabilidades como fracción 0–1.
- `size_bytes` son bytes, `sha256` lowercase hexadecimal sobre los bytes exactos.
- La solicitud no contiene rutas del filesystem ni credenciales.
- Se rechazan claves duplicadas en JSON y valores numéricos no estándar (`NaN`, `Infinity`).
- `RunResult.publishable` sólo es true para `success`; el exportador debe verificarlo antes de publicar.
- `validate_result(request, result, expected_core_commit)` enlaza `run_id`, manifiesto de entrada y commit del core fijado antes de aceptar una respuesta.
- `PublicPrediction` es una lista allowlisted. No colocar en ella features internas, razones de scoring, pesos, rutas ni IDs internos.
- `tests.test_sharpicks_contracts` cubre 12 casos unitarios de aceptación/rechazo; el CI del SHA `f53cd2646c219516293d195a4b6ab72b4fab6c68` todavía está en ejecución.

## Compatibilidad

Cambios aditivos opcionales sólo pueden incorporarse con pruebas de compatibilidad explícita. Cambiar tipos, significado, unidades, required fields o política de publicación requiere nueva versión de contrato. La v1 actualmente rechaza todo campo no declarado; este comportamiento es intencional.

## Pendiente

Definir DTOs separados para cuotas, features, resultados de partido, estado de modelos, calibración, entrenamiento, evaluación y metadatos de exportación; el v1 implementado aún no cubre esos flujos. Conectar el core privado y validar el mismo esquema desde ambos lados.
