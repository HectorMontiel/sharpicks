# Grafo inicial de dependencias por entrypoint

> Inspección estática de imports directos en 12 archivos de la rama principal. Es un mapa de primer nivel, no un SBOM ni un grafo transitivo completo. Los imports locales se identifican por nombre de módulo; imports de biblioteca estándar/terceros se conservan para el inventario de dependencias. Los imports dinámicos, subprocess, plugins, imports condicionales y rutas calculadas requieren inspección manual.

## 1. Entry points y módulos internos observados

| Entry point | Imports locales directos observados | Archivos/datos referenciados en el código | Variables de entorno leídas directamente | Clasificación |
|---|---|---|---|---|
| `pipeline_total.py` | `uefa_scraper`, `config`, `engines.tennis_engine`, `shadow_booster`, `transfermarkt_scraper`, `lineup_collector`, `player_db`, `backfill_stats`, `fotmob_scraper`, `clima` | `historico_partidos.csv` | no detectadas directamente | Core de ingesta/actualización |
| `bot_telegram.py` | `traductor_quant`, `reto_escalera`, `alpha_finder`, `guardia_barrido`, `formato_ia`, `mercados_dia`, `data_health` | `apuestas_{dia}.txt` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DEPORTES_ENVIO` | Motor de selección + gateway Telegram |
| `bot_dia_completo.py` | `bot_telegram`, `mercados_dia`, `formato_ia`, `alpha_finder`, `guardia_barrido` | `apuestas_{dia}.txt` | hereda indirectamente configuración del bot | Gateway Telegram |
| `league_engine.py` | `feature_engineering`, `features_v26`, `features_v59`, `mls_features`, `cdi_futbol`, `momentum_tactico`, `statsbomb_calibration`, `config`, `correlated_synthetic_generator`, `train_tda_model`, `api_football_manager`, `fbref_scraper_v3`, `uefa_scraper`, `name_mapper`, `leagues_cup`, `stats_espn`, `fixtures_espn`, `transfermarkt_scraper`, `meta_ensemble`, `remates_jugadores`, `prediction_api`, `modelos_remotos`, `modelos_portables`, `inferencia_rapida`, `cuotas_multi`, `calibracion_mercado`, `calibracion_elo`, `distributions`, `rendimiento_equipos`, `goleadores` | `modelos_familia.json`, históricos por liga, `modelo.joblib`, `escalador.joblib`, regresores, ROI, `team_stats_{clave}.json`, `odds_actuales.json`, `calibracion_statsbomb.json` | parámetros de reentreno y límites de histórico | Núcleo de modelos y scoring |
| `precalculo_dia.py` | `alpha_finder`, `resultados_fotmob`, `resultados_flashscore`, `mercado_sin_modelo`, `io_atomico`, `decisiones_dia`, `alias_equipos`, `alias_nombres`, `mercado_implicito`, `archivo_contexto`, `ventaja_ponches`, `partidos_jugados`, `dia_picks`, `tiros_equipo`, `tiros_seguimiento`, `analisis_seguimiento`, `arriesgadas`, `anunciadas`, `capa1_resultados` | `pronostico_dia.json` y URL remota de ese artefacto | banderas y timeout de precálculo, repo/rama de modelos | Core de selección y cache |
| `recalibrar_todo.py` | `build_ledger_deportes`, `build_ledger_total`, `build_pick_ledger`, `build_ledger_totales`, `calibracion_confianza`, `precision_ligas`, `edge_engine`, `validacion_deportes`, `recalibrate_from_history`, `autopsia`, `aprendizaje_continuo`, `calibrador_bandas`, `pronosticos_guardados`, `calibrador_goles`, `build_ledger_handicap`, `selector_apuestas`, `radar_capturas`, `radar_errores`, `memoria_equipos`, `io_atomico` | `recalibracion_estado.json`, ledgers CSV | no detectadas directamente | Core de calibración y evaluación |
| `exportar_web.py` | `nombres_ligas`, `decisiones_dia`, `config`, `errores_web`, `modo_modelo`, `partidos_jugados`, `precalculo_dia`, `tablas_web`, `espn_vivo`, `escudos`, `jugadores_prob`, `liquidar_pendientes`, `combinadas_web` | `hoy.json`, `premium.json`, `vip.json`, `analisis.json`, `cuotas_mx.json`, `tablas.json`, `meta.json` | `WEB_DATOS`, `WEB_PRIVADO`, `WEB_ANALISIS`, `SITIO_URL`, `PICK_ID_CLAVE`, `GITHUB_ACTIONS`, Supabase URL/service key y niveles premium | Exportador sensible / frontera pública |
| `respaldo_base.py` | imports estándar y `requests` | archivos JSON de salida de backup | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Operación sensible |
| `publicar_modelos.py` | `modelos_remotos`, `modelos_portables` | `modelos_publicados.json`, archivos `.joblib`, paquetes tar | `REPO_MODELOS`, `GITHUB_REPOSITORY`, `RELEASE_MODELOS` | Publicación controlada de modelos |
| `daily_snapshots.py` | `odds_store`, `cuotas_multi`, `fixtures_espn`, `name_mapper`, `config`, `league_engine`, `engines.kbo_engine` | `_v75_snapshots.json` | no detectadas directamente | Ingesta/snapshots privados |
| `radar_errores.py` | `radar_capturas` | `radar_errores.txt`, `radar_errores.json`, `pick_ledger.csv` | no detectadas directamente | Analítica interna |

## 2. Dependencias de terceros detectadas en los entrypoints

- Datos y ciencia: `pandas`, `numpy`, `scipy`, `scikit-learn`, `lightgbm`, `joblib`, `ripser`.
- Red y APIs: `requests`.
- Persistencia/archivos: `json`, `csv`, `tarfile`, `hashlib`, `hmac`.
- Runtime: Python 3.12 en la mayoría de workflows auditados; hay instalación Node/Deno en las validaciones web.

La lista no sustituye a `requirements.txt` ni determina dependencias transitivas. Se debe generar un lockfile reproducible y un SBOM por entorno cuando el core privado tenga un primer build.

## 3. Fronteras arquitectónicas recomendadas

### Paquete privado `sharpicks_core`

Candidatos para extraer tras pruebas de caracterización:

- `league_engine` y módulos de features, modelos, calibración y distribuciones.
- `alpha_finder`, `traductor_quant`, `edge_engine`, `selector_apuestas`, `mercados_dia`, `decisiones_dia`.
- `precalculo_dia`, `recalibrar_todo`, pipelines de ingesta y snapshots.
- artefactos de modelos, ledgers, históricos y parámetros propietarios.

### Adaptadores/gateways

Mantener interfaces pequeñas y con contratos:

- `CoreRunner`: recibe manifiesto + parámetros; devuelve artefacto versionado.
- `WebExporter`: transforma resultado interno a allowlist pública.
- `TelegramGateway`: valida canal/segmento y envía con clave de idempotencia.
- `SupabaseRepository`: repositorio con métodos explícitos; evitar pasar service key a scripts de scoring.
- `ArtifactStore`: carga/descarga por identificador inmutable y checksum.

### Orquestador público

- cron, workflow_dispatch, permisos, concurrency y timeout.
- validaciones sin secretos.
- descarga del paquete de salida con versión fija.
- verificación de manifiesto y checksum.
- despliegue de assets públicos sin incluir archivos internos.

## 4. Problemas que requieren revisión antes de extraer

1. **Imports circulares o alias:** `league_engine.py` importa `league_engine` además de muchos módulos locales; revisar si hay importación tardía deliberada.
2. **Acoplamiento por archivos:** los motores usan históricos y JSON por nombre de liga; el contrato debe pasar referencias lógicas, no depender del cwd.
3. **Estado global/config:** `config` aparece en varios entrypoints; separar configuración no secreta, secretos y defaults.
4. **Descarga remota:** `precalculo_dia.py` y modelos remotos hacen referencia a repositorios/URLs; pinning y checksum obligatorios.
5. **Exportador web:** importa directamente lógica de precálculo, tablas y liquidación. Antes de mover scoring, convertirlo en consumidor de un DTO público y evitar que la web importe el core.
6. **Bot Telegram:** el bot mezcla decisión/formato/envío. Extraer selección y mantener un gateway pequeño con validación de destino e idempotencia.
7. **Backups:** no compartir el workspace del core con el artefacto de respaldo; evitar que datos temporales aparezcan en logs o artifacts de Actions.

## 5. Próxima extracción segura: contrato antes que código

1. Definir JSON Schema de `RunRequest` y `RunResult`.
2. Crear fixtures sintéticos representativos para fútbol, NBA, tenis y otros deportes soportados.
3. Escribir un adaptador público que valide JSON, versión y checksum, sin importar ningún módulo privado.
4. Implementar el mismo contrato en una rama del core privado.
5. Ejecutar shadow mode: producción actual y core nuevo procesan el mismo input; no enviar ni publicar el resultado nuevo.
6. Comparar número de eventos, picks, probabilidades, cuotas, EV, stake/riesgo y razones de descarte.
7. Resolver diferencias con tests de caracterización antes de activar cualquier canary.

## 6. Límites de este análisis

- Se inspeccionaron imports directos de 12 entrypoints, no todos los 768 archivos Python.
- Los imports locales no se resolvieron recursivamente ni se verificaron por ejecución.
- No se inspeccionaron todos los imports dentro de ramas condicionales, `importlib`, `__import__`, subprocess o scripts lanzados por string.
- Los nombres de archivos son referencias literales detectadas, no inventario exhaustivo de I/O.
- Las variables de entorno son las lecturas directas detectadas en esos archivos; módulos importados pueden leer otras.
- El análisis se hizo sobre el código disponible en la rama principal en el momento de la consulta; este documento se añade a la rama de hardening.

Por estas limitaciones, este documento sirve para diseñar la extracción y priorizar inspecciones; no autoriza todavía a mover los módulos ni a eliminar los archivos originales.
