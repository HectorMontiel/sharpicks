# Backtesting v212 — la puerta de activación

Generado por `backtest_v212.py` el 2026-11-02 15:50.

## Criterios de activación (§7.3)

Una regla se activa **sola** si y sólo si cumple los cuatro. **No medible cuenta como no aprobado.**

| criterio | umbral |
|---|---|
| brier | <= baseline |
| p5 | >= 0 |
| hit_rate | >= baseline |
| roi | >= baseline |
| ruina_30d | <= 5% |

## Fuera de muestra (§7.4)

Los ledgers son walk-forward por construcción: `build_ledger_totales.py` recorta el entrenamiento a fechas estrictamente anteriores al pliegue de test. Reparto por pliegue:

| pliegue | picks |
|---|---|
| 0 | 19.376 |
| 1 | 18.120 |
| 2 | 16.907 |
| 3 | 15.706 |
| 4 | 16.544 |

## Modo Seguridad — A (baseline) vs B

| deporte | versión | n | Brier | ECE | hit rate | ROI | p5 | ruina 30d |
|---|---|---|---|---|---|---|---|---|
| Fútbol | A baseline | 58.226 | 0.2369 | 0.0086 | 0.4940 | -4.79 % | -5.49 % | +0.00 % |
| Fútbol | B seguridad | 3.218 | 0.2176 | 0.0106 | 0.6759 | +0.35 % | -1.72 % | +0.00 % |
| KBO | A baseline | 252 | 0.2431 | 0.0352 | 0.5675 | -0.58 % | -10.50 % | +0.00 % |
| KBO | B seguridad | 13 | 0.1703 | 0.2116 | 0.8462 | +31.08 % | — | — |
| NFL | A baseline | 539 | 0.2373 | 0.0454 | 0.5696 | +1.87 % | -5.24 % | +0.00 % |
| NFL | B seguridad | 49 | 0.2205 | 0.0181 | 0.6531 | +0.76 % | -16.50 % | +0.00 % |
| Tenis | A baseline | 27.636 | 0.2144 | 0.0329 | 0.6544 | -4.40 % | -5.20 % | +0.00 % |
| Tenis | B seguridad | 5.349 | 0.2264 | 0.0366 | 0.6483 | -5.64 % | -7.26 % | +0.00 % |

## Escalada de líneas 1,5 → 2,5 (la única con precio real)

| versión | n | Brier | ECE | hit rate | ROI | p5 |
|---|---|---|---|---|---|---|
| A baseline (todo Más de 2.5) | 41.112 | 0.2475 | 0.0076 | 0.5131 | -4.77 % | -5.56 % |
| C escalada (ref. superior) | 1.053 | 0.2403 | 0.0250 | 0.6068 | -4.51 % | -8.54 % |
| C escalada (ref. base) | 1.053 | 0.2403 | 0.0250 | 0.6068 | -4.51 % | -8.54 % |

## Decisión por regla (§7.6, §7.7)

| regla | estado | por qué |
|---|---|---|
| `modo_seguridad` | 🔴 apagada | no supera los criterios en ningún deporte con muestra suficiente |
| `escalada_lineas` | 🔴 apagada | la regla de 3 de 4 fuentes no se dispara ni una vez sobre el histórico: dos de sus cuatro fuentes no existen ahí (el xG del repositorio es sintético, y las señales de contexto de partidos pasados no se archivaron). No es que falle los criterios: es que no hay con qué evaluarla, y no medible cuenta como no aprobado. |
| `escalada_2_5_a_3_5` | 🔴 apagada | no existe cuota histórica de Más de 3,5 en ninguna fuente del proyecto (odds_historico.db sólo guarda la línea 2,5), así que el ROI de la línea que se apostaría no se puede medir. No medible cuenta como no aprobado. |
| `modo_seguridad_nfl` | 🔴 apagada | no existe ledger walk-forward de NFL: `historico_nfl.csv` tiene 1.095 partidos con resultado pero sin predicciones fuera de muestra ni cuota de ganador |
| `modo_seguridad_kbo` | 🔴 apagada | no existe ledger walk-forward de KBO y `historico_kbo.csv` (13.149 partidos) NO tiene ninguna columna de cuotas, así que el ROI es inmedible por construcción |

## Justificación escrita

### `modo_seguridad` — apagada

no supera los criterios en ningún deporte con muestra suficiente

- **Fútbol**: p5 de bootstrap negativo (-1.72%)
- **KBO**: muestra vacía o mínima
- **NFL**: roi empeora (0.0076 contra 0.0187); p5 de bootstrap negativo (-16.50%)
- **Tenis**: brier empeora (0.2264 contra 0.2144); hit_rate empeora (0.6483 contra 0.6544); roi empeora (-0.0564 contra -0.0440); p5 de bootstrap negativo (-7.26%)

### `escalada_lineas` — apagada

la regla de 3 de 4 fuentes no se dispara ni una vez sobre el histórico: dos de sus cuatro fuentes no existen ahí (el xG del repositorio es sintético, y las señales de contexto de partidos pasados no se archivaron). No es que falle los criterios: es que no hay con qué evaluarla, y no medible cuenta como no aprobado.

**Qué haría falta para poder decidirlo:** xG observado (FotMob cubre hoy 28 partidos) y un archivo de señales de contexto por partido, que sólo se puede construir hacia delante


### `escalada_2_5_a_3_5` — apagada

no existe cuota histórica de Más de 3,5 en ninguna fuente del proyecto (odds_historico.db sólo guarda la línea 2,5), así que el ROI de la línea que se apostaría no se puede medir. No medible cuenta como no aprobado.

**Qué haría falta para poder decidirlo:** cuotas de cierre de Más de 3,5, por partido, en al menos 1.000 partidos por competición


### `modo_seguridad_nfl` — apagada

no existe ledger walk-forward de NFL: `historico_nfl.csv` tiene 1.095 partidos con resultado pero sin predicciones fuera de muestra ni cuota de ganador

**Qué haría falta para poder decidirlo:** construir un ledger walk-forward de NFL, como `build_ledger_totales.py` hace con el fútbol


### `modo_seguridad_kbo` — apagada

no existe ledger walk-forward de KBO y `historico_kbo.csv` (13.149 partidos) NO tiene ninguna columna de cuotas, así que el ROI es inmedible por construcción

**Qué haría falta para poder decidirlo:** una fuente de cuotas históricas de KBO

