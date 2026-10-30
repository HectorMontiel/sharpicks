# Clasificación de activos y modelo de amenazas de SharPicks

> Documento de trabajo basado en el inventario visible del repositorio. No sustituye un escaneo de historial Git, análisis de secretos dedicado ni revisión de grants/RLS en staging.

## 1. Activos identificados

| Activo | Ejemplos observados en inventario | Riesgo si permanece público | Tratamiento |
|---|---|---|---|
| Código propietario | motores, scoring, calibración, reglas de picks | exposición de estrategia y ventaja competitiva | extraer a core privado |
| Modelos entrenados | artefactos `.joblib` bajo `modelos/` | ingeniería inversa, reutilización y exposición de features | almacenamiento privado, versionado y checksum |
| Históricos y snapshots | `corners_snapshots.csv`, `bajas_historico.csv`, `historico_partidos.csv`, `odds_snapshots.csv` | fuga de datos comerciales y reconstrucción de estrategia | clasificar, minimizar y mover |
| Cachés de plantillas/estadísticas | `team_stats*.json` y ficheros por liga | exposición de datos recopilados y lógica de features | sólo publicar vistas agregadas permitidas |
| Backups de Supabase | artifacts de Actions | aunque cifrados, el repositorio público aumenta la superficie de metadatos/retención y errores operativos | almacenamiento privado dedicado + restore probado |
| Payloads web | JSON exportados a `web/` | picks premium, IDs, datos de usuario o secretos si falla el filtro | allowlist explícita + test de fuga |
| Releases | paquetes y modelos publicados | exposición persistente fuera del árbol actual | inventario y política de retención |

El inventario previo detectó, entre otros, un modelo de aproximadamente 65.7 MB, un CSV de snapshots de corners de aproximadamente 104.6 MB, un histórico de bajas de aproximadamente 30 MB y unos 73 assets de release con aproximadamente 701 MB combinados. Son cifras aproximadas del corte auditado; deben recalcularse antes de planificar el traslado.

## 2. Actores y amenazas

- **Visitante anónimo:** descarga repositorio, historial, releases y artefactos públicos.
- **Fork/PR no confiable:** intenta ejecutar código modificado en workflows; puede aprovechar permisos o secretos expuestos a eventos incorrectos.
- **Credencial comprometida:** permite leer/escribir Supabase, publicar en Telegram, enviar correo o desplegar la web.
- **Proveedor externo degradado:** devuelve datos incompletos, stale, 429 o payloads alterados.
- **Error de exportación:** incluye un campo interno o datos premium en un JSON público.
- **Error de backup/restore:** backup cifrado pero incompleto, clave perdida, firma no verificada o procedimiento de restauración nunca probado.
- **Confusión de versiones:** el orquestador descarga un artefacto mutable o incompatible con el contrato del core.

## 3. Controles de seguridad objetivo

### Repositorios y Actions
- Mantener el orquestador público sin secretos del core.
- No conceder el token privado a eventos `pull_request` desde forks.
- Separar workflows de validación (sin secretos) y workflows de producción (entorno protegido).
- Fijar acciones externas a SHA completo cuando se complete la revisión de supply chain.
- Permisos mínimos por job: `contents: read` por defecto; `actions: write` sólo en el job que despacha workflows; `contents: write` sólo cuando se publican datos permitidos.
- Evitar checkout de PR no confiable en jobs que reciben secretos.

### Artefactos
- Artefactos privados fuera de Releases públicas.
- Cada artefacto con SHA-256, versión, fecha, clasificación y retención.
- Rechazar artefactos sin firma/checksum esperado.
- No ejecutar binarios ni scripts recibidos como resultados.
- Separar outputs públicos de logs, dumps, modelos y datasets privados.

### Supabase
- No aplicar cambios de RLS/grants directamente en producción durante la migración.
- Validar roles anon/authenticated/service_role, vistas SECURITY DEFINER, funciones RPC y Edge Functions en staging.
- Revisar explícitamente cada endpoint que use `verify_jwt=false`.
- Añadir autenticación/verificación de firma a webhooks sólo después de documentar el contrato real del proveedor y probar compatibilidad.
- Rotar credenciales sólo con despliegue coordinado y procedimiento de rollback.

### Backups
- AES-CBC requiere autenticación externa; la firma HMAC debe verificarse antes de descifrar/restaurar.
- Preferir cifrado autenticado moderno (por ejemplo AES-GCM o ChaCha20-Poly1305) en una futura versión con formato versionado.
- Separar claves de cifrado y firma, guardarlas fuera del mismo sistema de backup y documentar recuperación.
- Mantener al menos una copia fuera de GitHub Actions y ejecutar restore periódico en proyecto aislado.
- Probar integridad, conteos, relaciones, RLS y consultas críticas después del restore.

## 4. Riesgos críticos a cerrar antes de mover producción

| Riesgo | Severidad | Evidencia/estado | Gate |
|---|---|---|---|
| Código/modelos/datasets expuestos | Alta | inventario detectó artefactos grandes y código de scoring en repo público | inventario final + extracción y limpieza histórica |
| Backup sin restore validado | Crítica | no hay evidencia de restauración completa | restauración en Supabase aislado |
| Exportación accidental de datos privados | Alta | exportador usa service key y genera web payloads | allowlist + tests con datos sintéticos y secretos canario |
| Token privado en workflow de PR | Crítica | aún no existe integración privada | diseño de eventos y environment protection |
| Dependencia en artefactos mutable | Alta | contrato cross-repo todavía no implementado | SHA/manifest/firma y version pin |
| SQL hardening no probado | Alta | v546/v547 pendientes de staging | staging, explain/analyze y regresión RLS |
| Supply chain de Actions | Media/Alta | workflows usan tags de acciones | SHA pinning y Dependabot/renovate |
| Restauración de clave perdida | Crítica | respaldo usa secreto GitHub | custodia independiente y simulacro |

## 5. Criterios de aceptación de seguridad

- Ningún secreto de core presente en el repo público, sus releases, logs o artefactos.
- Ningún dataset/modelo privado servido por URL pública o cache CDN.
- Todos los workflows públicos de PR operan sin token privado.
- El core valida el llamador y el orquestador valida el resultado.
- Los payloads web y Telegram pasan una allowlist de campos.
- Restauración completa demostrada con una copia independiente.
- Rotación de claves y rollback ensayados.
- Auditoría histórica de secretos completada y hallazgos revocados/rotados.
