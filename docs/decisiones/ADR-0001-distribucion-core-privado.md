# ADR-0001: Distribución del core privado

- **Estado:** PROPUESTO; la integración no está activa.
- **Fecha:** 2026-10-30.
- **Ámbito:** cómo ejecuta el orquestador público código propietario durante jobs confiables.
- **Relacionados:** [arquitectura objetivo](../arquitectura/01_ARQUITECTURA_OBJETIVO.md), [estrategia de distribución](../arquitectura/03_ESTRATEGIA_DISTRIBUCION_CORE.md), contrato `sharpicks_contracts` v1.

## Contexto

Los workflows actuales y el código de SharPicks están acoplados a módulos y assets que se pretende alojar en `sharpicks-core`. El acceso a ese repositorio no está disponible en este entorno, por lo que aún no se conoce su estructura empaquetable ni puede probarse el flujo real. La separación no debe alterar predicciones ni exponer credenciales a código de pull requests no confiables.

## Opciones consideradas

| Opción | Seguridad | Operación | Versionado y rollback |
|---|---|---|---|
| Checkout de paquete Python privado por SHA completo | Token de lectura sólo en job protegido; código ejecuta en runner confiable | Baja complejidad inicial | SHA verificable y rollback a SHA previo |
| Wheel en release/registry privado | Descarga autenticada; checksum del artefacto | Requiere pipeline de build/publicación | Buena si el artefacto es inmutable y tiene manifiesto |
| API interna | No distribuye código al orquestador | Requiere hosting, auth, métricas y operación continua | Versionado de API, rollback de servicio |
| Rama/tag mutable | Credencial de lectura | Sencillo al inicio | Cambios no reproducibles; rechazado |

## Decisión propuesta

Empezar con el checkout del paquete privado desde `sharpicks-core`, fijado a un SHA completo y dentro de un GitHub Environment protegido. La credencial será sólo lectura para ese repositorio y estará ausente de todos los jobs `pull_request` y de código de forks. El contrato JSON validado permanece como interfaz entre orquestador y core. Evaluar el wheel privado después de probar builds repetibles; usar API sólo si se justifica separar procesos.

## Consecuencias

- El rollback de código selecciona un SHA previamente caracterizado; modelo y dataset se registran por separado con checksums y versiones.
- El paquete se descarga y ejecuta dentro del runner, por lo que un checkout seguro no vuelve confiable al código por sí mismo: el job debe ser de confianza, con permisos mínimos y sin ejecución desde PR/fork.
- Se requiere crear o dar acceso al repositorio privado, definir el paquete y fijar el primer SHA aprobado antes de activar un consumidor.
- La distribución elegida no extrae ni migra todavía los motores del repositorio público.

## Verificación necesaria para aceptar

1. Resolver `sharpicks-core` con el acceso corporativo normal y revisar su estructura/propietarios.
2. Construir e instalar el paquete en un job aislado fijado por SHA completo, sin token en URL, logs, caché o artefactos.
3. Validar import limpio, contrato v1, checksums y ejecución en modo sombra con fixtures sintéticos.
4. Comparar salida con baseline antes de cualquier uso de producción.
5. Ensayar rollback del SHA, modelo y manifiesto de datos.

Hasta cumplir estas pruebas y revisar el repositorio, esta ADR sigue propuesta. No activar `MODELOS_CORE_CONSUMERS_READY` ni publicar o desplegar por este ADR.
