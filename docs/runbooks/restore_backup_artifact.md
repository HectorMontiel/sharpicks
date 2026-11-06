# Restaurar un artifact de backup cifrado

- **Estado:** IMPLEMENTADO (verificación/autenticación y extracción segura); restauración de base real PENDIENTE.
- **Revisión:** 2026-10-30.

## Alcance

`tools/restore_backup_artifact.py` lee el formato actualmente producido por `.github/workflows/respaldo_base.yml`: un tar gzip cifrado con OpenSSL AES-256-CBC/PBKDF2 y el sidecar HMAC-SHA256. El script comprueba el HMAC antes de descifrar, rechaza rutas fuera de `respaldo/`, enlaces y archivos especiales, y extrae a un directorio nuevo. No se conecta a Supabase ni escribe tablas.

## Requisitos y límites

- Obtener el artifact y su sidecar `.hmac` de una ejecución autorizada del workflow. No modificar ni eliminar el artifact original.
- Usar el secreto `RESPALDO_CLAVE` desde un gestor de secretos en un equipo confiable. No pegarlo en terminal compartida, issue, log, documento o chat.
- OpenSSL disponible en `PATH`; el runtime CI es Ubuntu. La prueba de cifrado/descifrado real se ejecuta en ese runtime. En la estación local auditada OpenSSL no está instalado, así que el test integral queda omitido localmente.
- Usar almacenamiento local protegido con espacio suficiente. El directorio restaurado contiene datos en claro; se debe mantener fuera del repositorio y de carpetas sincronizadas públicamente.
- Un artifact auténtico y correctamente extraído no prueba que el esquema actual sea compatible ni que una restauración de base tenga éxito.

## Procedimiento aislado

1. Crear una carpeta temporal privada y descargar allí `sharpicks-YYYY-MM-DD.tgz.enc` y `sharpicks-YYYY-MM-DD.tgz.enc.hmac`.
2. Configurar `RESPALDO_CLAVE` sólo en el entorno de proceso mediante el gestor seguro habitual.
3. Escoger un destino nuevo, inexistente, fuera del checkout y sin datos preexistentes.
4. Ejecutar:

   ```powershell
   python tools/restore_backup_artifact.py `
     .\backup.tgz.enc `
     .\backup.tgz.enc.hmac `
     D:\secure-temp\sharpicks-restore
   ```

5. Si el comando devuelve error, no usar contenido parcial; el script elimina su staging temporal y no modifica el artifact. No desactivar la verificación de HMAC ni volver a cifrar un archivo para “arreglarlo”.
6. Revisar los JSON y los conteos del `resumen.json` en el entorno protegido. Antes de probar `respaldo_base.py --restaurar`, usar una base de staging desechable y comprobar manualmente proyecto, host y credenciales de destino; no usar producción.
7. Registrar checksum, identificador de ejecución, versión de esquema, conteos y resultado de restauración sin incluir filas, emails, tokens ni el secreto.

## Validación del código

`tests/test_restore_backup_artifact.py` cubre HMAC inválido (sin invocar OpenSSL), traversal y symlinks. Cuando OpenSSL está instalado también cifra un fixture sintético con los flags del workflow, lo descifra y verifica el contenido. Esta prueba no contiene datos de SharPicks.

## Riesgos residuales y rollback

- El formato vigente usa CBC más HMAC derivado de la misma frase; conservarla con entropía alta y restringir su acceso. No hay evidencia de su longitud/entropía y no se ha rotado.
- El script restaura el archive a archivos locales. El upsert de tablas en Supabase es un paso separado y no está validado contra staging.
- El sidecar actual permite verificar integridad/autenticidad sólo frente a quien posee la frase. No demuestra autoría independiente ni disponibilidad.
- Rollback del procedimiento: descartar el directorio local aislado y volver a usar intacto el artifact anterior. Nunca borrar artifacts históricos desde este runbook.
