# Auditoría de GitHub Actions

- **Estado:** OBSERVADO; fijación de Actions IMPLEMENTADA y VALIDADA en CI para el commit `bae8759973b2ef8f3d5c5c4ea38e2025a0caca46`.
- **Fecha:** 2026-10-30.
- **SHA base auditado:** `228c86a7fb03ed555465e56971170565f3029d9b`.
- **Alcance:** 18 workflows versionados en `.github/workflows/`; revisión de triggers, permisos declarados, acciones externas y usos sensibles a partir del YAML. No se tuvo acceso a los settings privados, secrets ni retenciones de la organización.

## Inventario confirmado

Se confirmaron los 18 nombres listados en [`00_LINEA_BASE.md`](00_LINEA_BASE.md). Hay flujos de CI/validación, publicación web, ingesta/precálculo, recalibración/reentrenamiento, bots, respaldo, vigilancia y coordinación entre workflows.

El inventario más detallado por flujo, con cadencias y scripts, está en [`INVENTARIO_DEPENDENCIAS_WORKFLOWS.md`](../INVENTARIO_DEPENDENCIAS_WORKFLOWS.md). Las cadencias allí son expresiones declaradas en YAML; no son prueba de ejecución puntual.

## Cadena de suministro de Actions

**Hallazgo P2, confirmado:** las referencias a Actions externas usaban tags mutables como `@v4`, `@v5`, `@v3` y `@v2`. Esto permite que el contenido resuelto por el tag cambie sin un diff en SharPicks.

**Corrección implementada:** las referencias se fijaron a los SHAs de commit que GitHub REST resolvió para esos tags el 2026-10-30. No se cambió la versión mayor ni la configuración de sus pasos.

| Action | Tag previo | SHA fijado |
|---|---|---|
| `actions/checkout` | v4 | `11d5960a326750d5838078e36cf38b85af677262` |
| `actions/setup-python` | v5 | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| `actions/upload-artifact` | v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| `actions/setup-node` | v4 | `49933ea5288caeca8642d1e84afbd3f7d6820020` |
| `actions/configure-pages` | v5 | `983d7736d9b0ae728b81ab479565c72886d7745b` |
| `actions/deploy-pages` | v4 | `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` |
| `actions/upload-pages-artifact` | v3 | `56afc609e74202658d3ffba0e8f6dda462b719fa` |
| `denoland/setup-deno` | v2 | `22d081ff2d3a40755e97629de92e3bcbfa7cf2ed` |

**Pendiente:** añadir Dependabot/Renovate o una revisión programada de updates para que los pins reciban actualizaciones deliberadas. La fijación por sí sola no mantiene las Actions al día.

## Permisos y exposición a eventos

- **OBSERVADO:** no hay uso de `pull_request_target` en estos 18 archivos.
- **OBSERVADO:** los workflows de validación de PR declaran `contents: read` y no referencian `secrets.*` en el YAML revisado. No encontré un workflow que entregue explícitamente un token del core privado.
- **OBSERVADO:** `cuotas_mx.yml` declara `contents: write` y `actions: write`; los workflows de cálculo/reentrenamiento tienen `contents: write`; `sitio_web.yml` declara `pages: write` e `id-token: write`. Requieren commits, dispatches y Pages en el mismo job y siguen pendientes de reducción por job.
- **MITIGACIÓN PARCIAL:** `relevo.yml` ya separa el job `esperar` (`contents: read`, hasta 330 minutos, sin token explícito) del job `disparar` (`actions: write`, máximo 5 minutos y token sólo en el paso de dispatch). El comportamiento de espera, cron, concurrencia y `workflow_dispatch` no cambia. El cambio estático aún requiere CI en esta rama.
- **OBSERVADO:** `respaldo_base.yml` y `sitio_web.yml` usan `workflow_run`. Ambos hacen checkout sin `ref` explícito; el YAML no muestra descarga de artifact del workflow fuente ni checkout de una referencia controlada por el PR. Esto reduce el riesgo de ejecutar directamente código de un PR, pero no sustituye una revisión de condiciones del evento, artefactos, settings y permisos efectivos en GitHub.
- **OBSERVADO:** workflows de respaldo, sitio, Telegram y vigilancia referencian secretos de Supabase, Telegram, Cloudflare, correo u otros servicios. El YAML sólo prueba nombres referenciados, no existencia, valor, alcance ni rotación. No se imprimieron valores.
- **PENDIENTE:** verificar el default de `GITHUB_TOKEN`, políticas de aprobación de environments, protección de rama, acceso de forks, configuración de Pages, scopes de secretos y quién puede ejecutar `workflow_dispatch`.

## Artefactos, escritura y operación

- `respaldo_base.yml` cifra el directorio generado con AES-256-CBC/PBKDF2 y crea HMAC-SHA256 antes de subir el archivo cifrado y su firma como artifact con retención de 30 días. La clave de firma se deriva de la misma frase de respaldo; no hay evidencia de restore aislado en este corte. La confidencialidad depende de la entropía y custodia de `RESPALDO_CLAVE`; retención y recuperación siguen sin validarse.
- `retrain_leagues.yml` declara `contents: write`, corre diariamente y tiene timeout de 150 minutos. El comentario del workflow describe publicación/actualización de modelos. Esta auditoría no ejecutó ese proceso.
- **Hardening de publicación de modelos en esta rama:** `publicar_modelos.py` requiere `REPO_MODELOS` explícito y confirma por API que el repositorio destino tenga `private=true` antes de crear/subir assets. El paso recibe el nombre del secret `CORE_RELEASE_TOKEN`; no se comprobó si el secret o variable existe. Si la publicación/verificación falla, el commit final omite `git add modelos/` y `.gitignore`. Retirar los pesos versionados requiere además `MODELOS_CORE_CONSUMERS_READY=true`, sin valor habilitado en esta rama. Tests locales cubren los gates; CI del nuevo head pendiente.
- `sitio_web.yml` publica datos mediante Supabase/Pages y tiene varios secretos de servicios. El propio YAML corre validadores antes del paso de exportación; eso no demuestra que el payload actual esté completamente allowlisted.
- `validate_sharpicks.yml` ejecuta la suite de `tests/`, pero antes no tenía filtros de ruta para `tests/**`, `tools/**`, `sharpicks_contracts/**` ni los módulos de distribución de modelos. Añadí esos filtros para PR y push de ramas `audit/**`. La rama autorizada recibe validación por su PR a `main`; no se añade un segundo trigger push redundante. No se cambiaron schedules ni operaciones productivas.
- Se observan referencias de Actions fijadas arriba; dependencias instaladas con `pip` y acciones de runtime no quedan cubiertas por el pin de Actions. No hay lockfile completo de Python.
- No se modificaron schedules, permisos, secretos, publicaciones ni workflows productivos en este cambio.

## Riesgos y acciones

| ID | Hallazgo | Severidad | Estado |
|---|---|---:|---|
| CI-01 | Tags de Actions mutables en 18 workflows | P2 | IMPLEMENTADO: pins por SHA; CI del nuevo SHA pendiente |
| CI-02 | Permisos de escritura declarados a nivel workflow en varios procesos | P2 | EN EJECUCIÓN: `relevo.yml` aisló Actions write al job corto de dispatch; otros flujos mixtos aún requieren revisión |
| CI-03 | Backup sólo tiene evidencia de generación/cifrado, no de restore | P1 | PENDIENTE: restore en entorno aislado |
| CI-04 | Secrets de producción referenciados desde workflows del repo público | P1 | OBSERVADO; no se detectó exposición de valores. Revisar entorno, aprobaciones y mínimo alcance |
| CI-05 | No hay pin/lock reproducible de dependencias Python y Deno | P2 | PENDIENTE |

## Validación

- `git diff --check`: aprobado para los cambios locales actuales.
- Validación YAML local: no ejecutada aún.
- Check GitHub Actions del PR antes de los pins: los jobs `instalar`, `tests` y `validar` estaban aprobados para el SHA base. No se consideran evidencia para un commit posterior.
- CI del commit `bae8759`: `instalar`, `tests` y `validar` aprobados en GitHub. Estos checks no incluyen los cambios locales posteriores del contrato.
- CI actualizado: la suite `unittest discover` cubre `tests/**` y sus herramientas/contratos ahora activan `validate_sharpicks.yml`. La ejecución GitHub para los commits recientes permanece en cola; esta ampliación aún no tiene resultado CI.
- Operación de workflows productivos: no ejecutada ni afirmada.

## Criterios de aceptación pendientes

1. CI del nuevo SHA aprueba y el diff no cambia triggers ni comandos de workflows.
2. Permisos efectivos y protecciones se verifican con settings de GitHub y se reducen por job con pruebas.
3. Backup se restaura en un destino aislado y los conteos/checksums se validan.
4. Los secrets se asignan sólo a environments protegidos y workflows que los necesitan.
