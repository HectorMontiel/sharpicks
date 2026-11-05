# ADR-0002: repo completo privado con runner propio en la nube

- **Estado:** ACEPTADO por el propietario el 2026-11-04, con tope de ~150 pesos al mes. Sin ejecutar: falta contratar el servidor, fusionar el PR y cambiar la visibilidad, cada paso con su autorización.
- **Fecha:** 2026-11-04.
- **Sustituye a:** ADR-0001 (separar el motor en `sharpicks-core`), si se acepta.

## Objetivo

Que el código, los modelos y los datos dejen de ser públicos sin pagar los minutos de Actions, sin depender de la PC del propietario y sin arriesgar las predicciones.

## Medición (CONFIRMADO, `tools/medir_actions.py`, 7 días al 2026-11-04)

| Concepto | Minutos/mes | Costo en privado con runners de GitHub |
|---|---:|---:|
| Todo | ~61,000 | ~US$354/mes |
| Sin el Relevo (runner dormido) | ~26,000 | ~US$144/mes |

Precio: US$0.006/min y US$12 incluidos en el plan Free (docs de GitHub, 2026-11). Trabajos a la vez, sin el Relevo: 0 el 48.7 % del tiempo, 1 el 40.9 %, 2 el 8.5 %, 3 o más el 1.9 %, pico de 5.

## Opciones

| Opción | Costo | Protege | Riesgo |
|---|---:|---|---|
| **A. Repo privado + servidor propio con runners** | precio de un servidor chico | Código, historia, modelos, datos, logs, artefactos | Hay que mantener un servidor; un solo punto de falla |
| B. Repo privado con runners de GitHub | ~US$144-354/mes | Todo | Costo |
| C. Motor en `sharpicks-core` y orquestador público (ADR-0001) | US$0 | Sólo lo nuevo, y con reservas | Ver abajo |
| D. Repo privado con runners en la PC | US$0 | Todo | El propietario ya lo descartó: depende de su PC |

## Decisión propuesta: A

Es lo mismo que ya operó del 29 de octubre (v510-v519) con runners en la PC, así que el código ya soporta el repo privado; lo único que cambia es dónde corre la máquina.

### Por qué no C

1. **No protege lo ya publicado.** Todo el código sigue en la historia del repo público. Sólo sirve si además se reescribe la historia o se abandona ese repo.
2. **Logs y artefactos públicos.** Los logs de un repo público los lee cualquiera, y los artefactos los baja cualquier cuenta. Un `print` o un error del motor privado saldría ahí.
3. **Salidas públicas.** Los flujos publican cuotas y precálculo con commits al repo. Habría que mover todo a otro almacén con un token de escritura.
4. **Riesgo de regresión.** 773 archivos, 1,925 dependencias y 11 ciclos: mover el motor por partes arriesga cambiar predicciones sin ganar protección adicional sobre A.
5. **Términos de GitHub.** Prohíben usar Actions «as part of a serverless application» y limitan los runners de GitHub a actividad del proyecto del repo. Un repo público que sólo existe para correr gratis código privado aumenta el riesgo de que restrinjan la cuenta, y con ella toda la operación. Esa restricción de «serverless» aplica también con runner propio; el uso actual de Actions como programador de producción ya está en esa zona.

## Servidor elegido por presupuesto

**Contabo Cloud VPS 4** (4 vCPU, 8 GB, 100 GB SSD, tráfico con uso justo), según su página al 2026-11-04: €5.50 al mes con contrato mensual y cuota inicial de monto no mostrado, o desde €4.40 al mes con contrato de 24 meses. Hetzner queda fuera: su plan equivalente cuesta €35.99 al mes.

**HIPÓTESIS sin medir:** que 8 GB y 100 GB alcancen y que su rendimiento sostenga las duraciones actuales. Por eso se contrata primero un mes y se hace la semana de prueba antes de comprometer 24 meses.

## Qué ya está hecho en la rama (IMPLEMENTADO)

- `vars.RUNNER_PESADO` en 12 flujos: sin la variable todo sigue igual. Con ella, los pesados pasan al servidor. Quedan en GitHub los ligeros y la instalación limpia (~1,250 min/mes, dentro de los ~2,000 incluidos).
- El Relevo no se reescribe: dormido en un runner propio no cuesta nada.
- `tools/vps_runner/instalar.sh`: prepara el servidor. **No probado en un servidor real.**
- `vigia_limites.yml` y `precalculo_dia.py` ya no fallan con el repo privado.

## Lo que NO resuelve (riesgo residual)

- Quien ya clonó el repo conserva esa copia. Hacerlo privado no la borra. La API no reporta forks al 2026-11-04.
- GitHub Pages deja de publicarse en el plan Free. El sitio canónico es Cloudflare y esos pasos ya tienen `continue-on-error`.
- Secret Scanning de GitHub deja de ser gratis en privado; queda `tools/secret_scan.py`.
- La app vieja de Streamlit Cloud necesitaría acceso al repo privado y un token para leer el precálculo.
- El repo crece ~1 GB por semana por los commits de datos; hay que vigilar el disco del servidor y el tamaño del repo.

## Reversa

Borrar la variable `RUNNER_PESADO` regresa a runners de GitHub. Volver el repo a público es posible, pero sólo tiene sentido si se apaga el servidor y se acepta exponer otra vez lo que haya cambiado.

## Criterios para aceptar

1. Servidor corriendo los flujos con el repo aún público, una semana sin fallos y con duraciones comparables.
2. Sólo entonces, cambiar la visibilidad; verificar que sitio, modelos, Telegram y respaldo sigan funcionando.
