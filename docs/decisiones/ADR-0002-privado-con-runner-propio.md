# ADR-0002: repo completo privado con runner propio en la nube

- **Estado:** ACEPTADO por el propietario el 2026-11-04 (servidor propio). Sin ejecutar: falta confirmar y contratar el servidor, fusionar el PR y cambiar la visibilidad.
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

## Servidor recomendado (revisado 2026-11-04)

El propietario quitó el tope de ~150 pesos: la prioridad es que no sea más lento ni falle. Sigue pendiente su confirmación.

**Referencia actual (CONFIRMADO, docs de GitHub):** cada trabajo tiene 4 CPU y 16 GB en repo público. En privado, los runners de GitHub bajan a 2 CPU y 8 GB, así que pagar por ellos además sería más lento. Sin el Relevo corren 2 trabajos o menos el 98 % del tiempo; igualar eso pide unos 8 núcleos.

**Evidencia de carga (OBSERVADO, octubre):** los 4 runners operaron en la PC con 6 procesadores y 6 GB; el precálculo rápido tardó 2.7 min contra ~10 en GitHub. Otra máquina puede rendir distinto.

| Plan | Núcleos | Memoria | Disco | Precio en su página |
|---|---:|---:|---:|---:|
| OVH VPS-4 (siguiente escalón) | 8 | 24 GB | 200 GB NVMe | desde US$23.37/mes |
| Contabo Cloud VPS 8 | 8 | 24 GB | 150 GB NVMe | ~€14/mes (cifra reconstruida) |
| Contabo VDS M (núcleos dedicados) | 8 | 32 GB | 240 GB NVMe | €68/mes (sin confirmar) |
| Hetzner CCX33 (dedicados) | 8 | 32 GB | 240 GB NVMe | €138.99/mes, no disponible |
| DigitalOcean dedicado | 8 | 32 GB | 100 GB SSD | US$252/mes |

**Actualización:** el propietario prefiere empezar más chico y barato. Punto de partida recomendado: **OVH VPS-3** (6 núcleos, 12 GB, 100 GB NVMe, desde US$12.32/mes en su página), con 3 runners; similar a los 6 procesadores con los que operó en la PC. Con 2 trabajos a la vez cada uno tendría menos núcleos que hoy (8.5 % del tiempo).

OVH VPS-4 queda como siguiente escalón por relación de capacidad, precio y disponibilidad publicada (99.9 %). Faltan por confirmar en su compra: región en EUA, impuestos y permanencia, porque esos datos no aparecieron en la parte legible de la página.

**Despertador:** el 29-oct, con el repo privado, GitHub no disparó los `schedule` (0 corridas en 5 h) y los lanzaba un despertador en la PC. Ya está portado a `tools/vps_runner/despertador.sh`, con temporizador de systemd cada 15 min. Se activa con la variable `DESPERTADOR=activo`; sin ella sólo anota. Activo, `telegram_bot` y `telegram_dia_completo` se saltan su cron para no mandar dos veces. Probado con un `curl` falso, no en un servidor real.

**Disponibilidad:** ningún proveedor garantiza 100 %. El servidor no guarda nada único: se reconstruye con `instalar.sh`. Si cae, borrar `RUNNER_PESADO` regresa los flujos a GitHub, con menos potencia y cobro por minuto.

**Apps de iOS y Android:** los usuarios llegan a Supabase y Cloudflare, no a este servidor. Más usuarios no cargan los runners; el límite a vigilar es Supabase (`vigia_limites.py`).

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
