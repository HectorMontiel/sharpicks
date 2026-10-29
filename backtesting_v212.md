# Backtesting v212 — la puerta de activación

Generado por `backtest_v212.py` el 2026-10-26 13:01.

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
| 0 | 18.757 |
| 1 | 17.667 |
| 2 | 17.266 |
| 3 | 17.178 |
| 4 | 18.429 |

## Modo Seguridad — A (baseline) vs B

| deporte | versión | n | Brier | ECE | hit rate | ROI | p5 | ruina 30d |
|---|---|---|---|---|---|---|---|---|
| Fútbol | A baseline | 60.922 | 0.2366 | 0.0093 | 0.4938 | -5.02 % | -5.72 % | +0.00 % |
| Fútbol | B seguridad | 3.649 | 0.2178 | 0.0101 | 0.6736 | +0.15 % | -1.79 % | +0.00 % |
| KBO | A baseline | 252 | 0.2423 | 0.0380 | 0.5714 | +1.74 % | -8.09 % | +0.00 % |
| KBO | B seguridad | 12 | 0.2349 | 0.0377 | 0.5833 | -8.67 % | — | — |
| NFL | A baseline | 539 | 0.2388 | 0.0335 | 0.5807 | +5.75 % | -1.95 % | +0.00 % |
| NFL | B seguridad | 44 | 0.2315 | 0.0267 | 0.6364 | +0.75 % | -17.67 % | +0.00 % |
| Tenis | A baseline | 27.584 | 0.2146 | 0.0333 | 0.6543 | -4.37 % | -5.19 % | +0.00 % |
| Tenis | B seguridad | 5.332 | 0.2270 | 0.0392 | 0.6461 | -5.95 % | -7.51 % | +0.00 % |

## Escalada de líneas 1,5 → 2,5 (la única con precio real)

| versión | n | Brier | ECE | hit rate | ROI | p5 |
|---|---|---|---|---|---|---|
| A baseline (todo Más de 2.5) | 40.838 | 0.2472 | 0.0069 | 0.5126 | -4.76 % | -5.58 % |
| C escalada (ref. superior) | 1.064 | 0.2363 | 0.0064 | 0.6250 | -1.74 % | -5.51 % |
| C escalada (ref. base) | 1.064 | 0.2363 | 0.0064 | 0.6250 | -1.74 % | -5.51 % |

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

- **Fútbol**: p5 de bootstrap negativo (-1.79%)
- **KBO**: muestra vacía o mínima
- **NFL**: roi empeora (0.0075 contra 0.0575); p5 de bootstrap negativo (-17.67%)
- **Tenis**: brier empeora (0.2270 contra 0.2146); hit_rate empeora (0.6461 contra 0.6543); roi empeora (-0.0595 contra -0.0437); p5 de bootstrap negativo (-7.51%)

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

