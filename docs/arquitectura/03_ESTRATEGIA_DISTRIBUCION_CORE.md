# Estrategia de distribución de `sharpicks-core`

- **Estado:** IMPLEMENTADO PARCIALMENTE; el publicador ahora exige y verifica destino privado, pero el core no se pudo resolver y no hay integración privada validada.
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

## Protección incorporada al flujo de publicación

- `publicar_modelos.py` ya no infiere el destino desde `GITHUB_REPOSITORY` ni cae al repositorio público. Requiere `REPO_MODELOS=owner/repo` y consulta la API GitHub para confirmar `private=true` antes de crear o subir Release assets.
- El paso de publicación usa el secret `CORE_RELEASE_TOKEN` y la variable `REPO_MODELOS`; si falta cualquiera o el destino no es privado/accesible, falla antes de cualquier operación de escritura.
- El workflow no hace `git add modelos/` ni actualiza `.gitignore` después de una publicación fallida. Además requiere la variable `MODELOS_CORE_CONSUMERS_READY=true` para retirar modelos del árbol público, incluso si el upload privado se verificó.
- Para una configuración futura, `CORE_RELEASE_TOKEN` debe ser un GitHub App/fine-grained token limitado al repo privado con permisos de contenido necesarios para Release (lectura de metadata y escritura de assets). Nunca se configura por chat. La variable de readiness no se debe activar hasta validar los consumidores de descarga en los workflows de producción.
- Estos gates sólo se prueban localmente con respuestas simuladas. No demuestran que `sharpicks-core`, la variable ni el secret existan; producción no fue ejecutada.

## Gates

- No pin mutable; el workflow debe recibir SHA completo.
- Scope de token limitado a lectura de Contents del único repo.
- Ningún token en PR/fork, artifacts, cachés o logs.
- Build reproducible de wheel, checksum y manifiesto.
- Prueba de importación limpia y predicción fixture en runner aislado.
- Comparación sombra contra baseline predictivo antes de usar salida.
- Rollback de versión de paquete/modelo ensayado.
