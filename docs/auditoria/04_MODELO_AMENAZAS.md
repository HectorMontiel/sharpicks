# Modelo de amenazas de SharPicks

- **Estado:** OBSERVADO + RECOMENDADO; modelo preliminar basado en el árbol público y workflows visibles.
- **Fecha/SHA:** 2026-10-30 / `228c86a7fb03ed555465e56971170565f3029d9b`.
- **Alcance:** confidencialidad del core/datos, integridad de picks/entitlements, credenciales, workflows y continuidad. No sustituye pruebas de penetración ni auditoría de configuración de la cuenta.

## Activos y superficies

| Activo | Superficie de ataque |
|---|---|
| Código predictivo y modelos | Repo e historial público, releases, artifacts, caches, instalación y carga de modelos |
| Históricos, cuotas y features | Archivos versionados, snapshots, jobs de ingesta, proveedores y backups |
| Picks, premium/VIP y datos de usuario | Exportador web, API/Edge Functions, tablas/vistas Supabase y Telegram |
| Secrets de Supabase/Telegram/pagos/correo/Cloudflare | Workflows, logs, forks, artifacts, aplicaciones de despliegue y operadores |
| Base de datos y pagos | RLS, RPC `SECURITY DEFINER`, vistas, webhooks y credenciales service role |
| Web pública | Exportación JSON, CDN/cache, GitHub/Cloudflare Pages, scripts cliente |
| Continuidad | GitHub Actions artifacts, almacenamiento de respaldo, clave y restauración |

## Actores

- Visitante que descarga repo/release público.
- Autor de fork/PR no confiable.
- Cuenta GitHub o secreto de Actions comprometido.
- Usuario autenticado que intenta acceder a recursos ajenos o manipular pagos.
- Proveedor externo con fallas, datos manipulados o rate limits.
- Error operativo de SharPicks o cambio incompatible de contrato/modelo.

## Riesgos priorizados

| ID | Amenaza | Probabilidad | Impacto | Prioridad | Controles observados | Mitigación/estado |
|---|---|---|---|---|---|---|
| TH-01 | Descarga/reconstrucción de estrategia y activos desde el repo público | Alta | Alto | P1 | Repo público, 5 modelos, grandes históricos y 73 assets de release visibles | Core privado; migrar sin pérdida, validar y luego retirar/purgar con plan específico. Pendiente |
| TH-02 | Secreto filtrado por workflow/log/artifact o permiso excesivo | Media | Crítico | P1 | Workflow YAML usa secrets context; no se inspeccionan values/settings. Validadores PR revisados no referencian secrets | Environments protegidos, permisos por job, audit histórico de secretos y rotación coordinada. Pendiente |
| TH-03 | Entitlement o datos de usuario incorrectos por acceso RLS/RPC/vista | Media | Alto | P1 | Migraciones muestran RLS y funciones definidoras; no hay prueba de ACL desplegada | Matriz anon/auth/service-role en staging, pruebas de RPC/vistas y control de identity. Pendiente |
| TH-04 | Publicación de datos premium/privados en JSON o CDN | Media | Alto | P1 | `exportar_web.py` produce varios payloads y usa service key según grafo/workflow | DTO allowlist, tests con canarios y revisión de payload real antes de publicación. Pendiente |
| TH-05 | Alteración/replay de webhook de pagos | Media | Alto | P1 | Stripe valida firma en código; Mercado Pago recupera estado consultando API del proveedor, sin validación de firma visible | Verificar protocolo/configuración desplegada, control de replay e idempotencia en staging. No se confirma explotación |
| TH-06 | Backup cifrado imposible de restaurar o manipulado | Media | Crítico | P1 | Workflow cifra con CBC y deriva HMAC de la misma frase; no hay evidencia de restore | Formato versionado autenticado, custodia separada y restore aislado. Pendiente |
| TH-07 | Supply-chain comprometida vía tag mutable de Action | Media | Alto | P2 | Tags de Actions estaban en workflows | Pins de SHA implementados en `bae8759`; CI de `601e52a` en curso |
| TH-08 | Modelo/dataset mutable o incompatible | Media | Alto | P2 | `.joblib` junto con versiones de bibliotecas fijadas parcialmente en `requirements.txt` | Manifiesto/hash/runtime/schema y promoción/rollback versionados. Pendiente |
| TH-09 | Proveedor degradado/incompleto genera pick incorrecto o duplicado | Media | Alto | P2 | Workflows ejecutan ingesta y selección; faltan contratos comunes confirmados | Frescura, idempotencia, alertas, pruebas de proveedor y comparación de regresión. Pendiente |

## Controles residuales y criterios de aceptación

- Confirmar que ningún token privado recibe código de fork/PR no confiable.
- Inventariar release assets, artifacts, logs y caches históricos; revisar permisos efectivos.
- Demostrar allowlist y ausencia de canarios en web/Telegram.
- Demostrar pruebas RLS/RPC por rol y verificación de webhooks en staging.
- Demostrar hash, firma, restauración y compatibilidad de modelos/backups.
- Registrar riesgo residual con responsable/fecha luego de pruebas; no reducir prioridad sin evidencia.
