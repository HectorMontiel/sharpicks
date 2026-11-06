# Rendimiento y costos de GitHub Actions

- **Estado:** CONFIRMADO con API de GitHub, 7 días al 2026-11-04. Se repite con `python tools/medir_actions.py --dias 7`.
- **Evidencia:** [`medicion_actions.json`](medicion_actions.json).
- **Unidad:** minutos por trabajo (`started_at` a `completed_at`). Es una estimación de lo que se factura en privado; hoy el repo es público y no se factura. GitHub redondea cada trabajo hacia arriba, así que la cifra real sería algo mayor.

| Concepto | Minutos/mes | US$/mes en privado con runners de GitHub |
|---|---:|---:|
| Todo | ~61,000 | ~354 |
| Sin el Relevo | ~26,000 | ~144 |

## Hallazgo principal

El Relevo es el 57 % de los minutos por trabajo: un runner durmiendo ~70 minutos entre barridos de cuotas para esquivar los cortes del cron de GitHub. En un repo público o en un runner propio no cuesta nada; con runners de GitHub en privado costaría ~US$210/mes.

## Simultaneidad (sin el Relevo)

| Trabajos a la vez | % del tiempo |
|---:|---:|
| 0 | 48.7 |
| 1 | 40.9 |
| 2 | 8.5 |
| 3 o más | 1.9 |

Pico: 5. Con 3 runners de trabajo más 1 para el Relevo, casi nada haría cola. **HIPÓTESIS:** 4 vCPU y 8 GB alcanzan; la memoria real de los picos no se ha medido y se valida en la semana de prueba.

## Pendiente

- Medir memoria y CPU reales en el servidor.
- Bajar el crecimiento del repo (~1 GB por semana por commits de datos).
