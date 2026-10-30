# Estrategia de distribución de `sharpicks-core`

- **Estado:** RECOMENDADO; no integrado por falta de repositorio privado resoluble.
- **Fecha:** 2026-10-30.

## Alternativas

| Alternativa | Seguridad | Coste/latencia | Versionado/rollback | Decisión |
|---|---|---|---|---|
| Python package privado desde Git, instalado por commit SHA | Token sólo lectura en Environment; requiere checkout y runner confiable | Bajo; el código se descarga al runner | Alta trazabilidad por SHA; rollback a commit anterior | **Elegida para primera migración** |
| Release privado/wheel versionado | Token para descargar release; requiere publicar y validar checksum | Bajo en runtime; CI de publicación adicional | Muy buena si artifacts inmutables y manifests | Evolución después del primer paquete |
| API interna | Auth de servicio, operación de red, superficie remota | Latencia, hosting/observabilidad/costos continuos | Versionamiento de API explícito, rollback requiere despliegue | Posponer hasta que se justifique separar procesos |
| Paquete instalado desde rama/tag mutable | Riesgo de cambio sin revisión | Bajo | Débil | Rechazada |

## Implementación prevista

1. `sharpicks-core` declara un paquete instalable y ejecutable con entrypoint versionado.
2. Workflow de producción/entorno protegido hace checkout de `HectorMontiel/sharpicks-core` a una carpeta separada y a un commit SHA validado. No introducir credenciales en URL de `pip`, línea de comando ni logs.
3. Token GitHub App o fine-grained limitado a `Contents: read` del repo privado se inyecta sólo en jobs de confianza mediante GitHub Environment; los jobs `pull_request` continúan sin acceso.
4. El orquestador valida `RunRequest`, el core comprueba checksums de inputs, genera `RunResult`; el lado público vuelve a validar versión, output manifest y allowlist.
5. Registrar commit de core, versión de paquete, modelo, esquema de features, dataset y SHA-256. Al fallar una promoción, volver a combinación de SHA/tag/modelo previamente aprobada.

## Por qué no se activa ahora

La API de GitHub devolvió `Could not resolve to a Repository` para `HectorMontiel/sharpicks-core`. No puede confirmarse si no existe o si falta acceso. No se configura un token improvisado ni se pide por chat. El contrato público queda probado localmente; la conexión de core y el primer workflow de sombra siguen BLOQUEADOS hasta que el repo esté disponible.

## Gates

- No pin mutable; el workflow debe recibir SHA completo.
- Scope de token limitado a lectura de Contents del único repo.
- Ningún token en PR/fork, artifacts, cachés o logs.
- Build reproducible de wheel, checksum y manifiesto.
- Prueba de importación limpia y predicción fixture en runner aislado.
- Comparación sombra contra baseline predictivo antes de usar salida.
- Rollback de versión de paquete/modelo ensayado.
