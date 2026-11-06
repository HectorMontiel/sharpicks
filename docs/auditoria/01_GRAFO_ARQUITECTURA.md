# Resultado del grafo estático de imports Python

- **SHA analizado:** `4c1223a635ed628798e547645209cba67582f65b`
- **Estado:** OBSERVADO; análisis estático, no grafo de ejecución completo.
- **Método:** AST de archivos Python; no importa ni ejecuta SharPicks.

## Métricas

| Medida | Resultado |
|---|---:|
| Archivos Python | 773 |
| Módulos/nombres de módulo | 773 |
| Aristas locales resueltas | 1925 |
| Import statements no resueltos localmente | 5063 |
| No locales de biblioteca estándar | 3626 |
| No locales de dependencias directas declaradas | 1430 |
| No locales opcionales/no clasificados | 7 |
| Sitios de import/evaluación dinámica | 2 |
| Llamadas a subprocess/os.system | 77 |
| Referencias estáticas a archivos | 2997 |
| Lecturas candidatas de entorno | 213 |
| Llamadas candidatas durante import | 8645 |
| Errores de parseo AST | 0 |
| Nombres de módulo duplicados | 0 |
| Componentes cíclicos | 11 |
| Entry points con __main__ o workflow | 581 |
| Scripts Python llamados literalmente por workflow | 44 |
| Módulos sin pista heurística por nombre/ruta | 432 |

Las etiquetas siguientes son pistas heurísticas por nombre/ruta; requieren confirmación por imports, I/O y efectos reales.

| Pista de responsabilidad | Módulos/archivos coincidentes |
|---|---:|
| `automation` | 5 |
| `configuration` | 3 |
| `core_predictive` | 26 |
| `data_ingestion` | 32 |
| `evaluation_and_backtesting` | 19 |
| `integrations` | 2 |
| `machine_learning` | 42 |
| `observability` | 7 |
| `odds_and_markets` | 48 |
| `pick_management` | 25 |
| `presentation` | 8 |
| `statistics` | 11 |
| `testing` | 151 |

## Entry points detectados

| Archivo | Descubrimiento | Workflows | Módulos transitivos resueltos |
|---|---|---|---:|
| `_v100_backtest_leagues_cup.py` | __main__ guard | — | 75 |
| `_v100_localia_leagues_cup.py` | __main__ guard | — | 74 |
| `_v101_ab_contexto_futbol.py` | __main__ guard | — | 1 |
| `_v101_ab_contexto_neto.py` | __main__ guard | — | 4 |
| `_v101_ab_contexto_tenis.py` | __main__ guard | — | 32 |
| `_v101_auditoria_empate.py` | __main__ guard | — | 2 |
| `_v101_auditoria_tenis.py` | __main__ guard | — | 33 |
| `_v101_descomponer_escalon.py` | __main__ guard | — | 3 |
| `_v101_fuga_fatiga_wta.py` | __main__ guard | — | 31 |
| `_v101_validar_aprendizaje.py` | __main__ guard | — | 2 |
| `_v102_ab_capa2.py` | __main__ guard | — | 2 |
| `_v102_ab_idf_futbol_nba.py` | __main__ guard | — | 3 |
| `_v102_ab_idf_nba_motor.py` | __main__ guard | — | 10 |
| `_v103_ab_conocimiento.py` | __main__ guard | — | 0 |
| `_v103_curva_ev_prob.py` | __main__ guard | — | 0 |
| `_v104_ab_abridor_kbo.py` | __main__ guard | — | 1 |
| `_v104_ab_abridor_kbo_limpio.py` | __main__ guard | — | 1 |
| `_v104_ab_nivel_liga.py` | __main__ guard | — | 2 |
| `_v104_ab_w_adaptativo.py` | __main__ guard | — | 1 |
| `_v104_ab_w_por_defecto.py` | __main__ guard | — | 0 |
| `_v105_ab_elo_global.py` | __main__ guard | — | 3 |
| `_v105_edge_line_shopping.py` | __main__ guard | — | 0 |
| `_v114_medir_exchanges.py` | __main__ guard | — | 26 |
| `_v114_profundizar.py` | __main__ guard | — | 0 |
| `_v114_sondeo_casas.py` | __main__ guard | — | 0 |
| `_v114_validar_emparejado.py` | __main__ guard | — | 26 |
| `_v115_calibrar_ponches.py` | __main__ guard | — | 28 |
| `_v115_encogimiento_ponches.py` | __main__ guard | — | 0 |
| `_v118_calibrar_mlb.py` | __main__ guard | — | 26 |
| `_v118_cobertura_remates.py` | __main__ guard | — | 27 |
| `_v125_gate_por_liga.py` | __main__ guard | — | 0 |
| `_v126_roi_tenis_mlb.py` | __main__ guard | — | 0 |
| `_v149_perfil_barrido.py` | __main__ guard | — | 129 |
| `_v149_perfil_cuotas.py` | __main__ guard | — | 26 |
| `_v152_cobertura_stats.py` | __main__ guard | — | 74 |
| `_v152_corners_modelo.py` | __main__ guard | — | 74 |
| `_v152_corners_sesgo.py` | __main__ guard | — | 74 |
| `_v153_auditar_frescura.py` | __main__ guard | — | 26 |
| `_v154_paralelismo.py` | __main__ guard | — | 26 |
| `_v154_perfil_barrido.py` | __main__ guard | — | 129 |
| `_v154_perfil_futbol.py` | __main__ guard | — | 26 |
| `_v156_corners_avanzado.py` | __main__ guard | — | 74 |
| `_v157_corners_multiplicativo.py` | __main__ guard | — | 74 |
| `_v157_fotmob_corners.py` | __main__ guard | — | 74 |
| `_v157_techo_senal.py` | __main__ guard | — | 74 |
| `_v158_corners_equipo.py` | __main__ guard | — | 74 |
| `_v163_cobertura_remates.py` | __main__ guard | — | 74 |
| `_v163_contencion_enganosa.py` | __main__ guard | — | 74 |
| `_v163_cuota_posicional.py` | __main__ guard | — | 76 |
| `_v163_emparejado_jugadores.py` | __main__ guard | — | 74 |
| `_v163_remates_estimadores.py` | __main__ guard | — | 74 |
| `_v163_remates_estimados.py` | __main__ guard | — | 75 |
| `_v163_remates_jugador.py` | __main__ guard | — | 75 |
| `_v163_remates_total.py` | __main__ guard | — | 75 |
| `_v163_resolver_equipos.py` | __main__ guard | — | 74 |
| `_v163_sondeo_alineacion.py` | __main__ guard | — | 27 |
| `_v163_sondeo_fotmob_lineup.py` | __main__ guard | — | 74 |
| `_v163_valida_ficha_remates.py` | __main__ guard | — | 230 |
| `_v163_verificar_lector_lineup.py` | __main__ guard | — | 75 |
| `_v164_auditar_destacada.py` | __main__ guard | — | 177 |
| `_v164_donde_se_pierde.py` | __main__ guard | — | 74 |
| `_v164_emparejar_lineas.py` | __main__ guard | — | 74 |
| `_v164_lambda_contra_casa.py` | __main__ guard | — | 74 |
| `_v164_sondeo_mercados_jugador.py` | __main__ guard | — | 26 |
| `_v164_valida_tarjeta.py` | __main__ guard | — | 171 |
| `_v165_emparejado_casa.py` | __main__ guard | — | 75 |
| `_v165_medir_cordura.py` | __main__ guard | — | 172 |
| `_v166_umbral_cordura.py` | __main__ guard | — | 0 |
| `_v169_goles_y_eficacia.py` | __main__ guard | — | 2 |
| `_v170_alfa_por_liga.py` | __main__ guard | — | 0 |
| `_v171_catalogo_playdoit.py` | __main__ guard | — | 75 |
| `_v175_goles_binomial_negativa.py` | __main__ guard | — | 0 |
| `_v175_h2h_en_la_lambda.py` | __main__ guard | — | 0 |
| `_v177_sesgo_goles_por_liga.py` | __main__ guard | — | 0 |
| `_v178_diag_manana.py` | __main__ guard | — | 0 |
| `_v178_historicos_encogidos.py` | __main__ guard | — | 0 |
| `_v178_manana_filtro.py` | __main__ guard | — | 171 |
| `_v178_perfil_pantalla.py` | __main__ guard | — | 0 |
| `_v178_perfil_primera.py` | __main__ guard | — | 177 |
| `_v178_repro_parlay_base.py` | __main__ guard | — | 177 |
| `_v178_restaurar_leagues_cup.py` | __main__ guard | — | 0 |
| `_v179_avisos_bundesliga.py` | __main__ guard | — | 0 |
| `_v179_champions_fuentes.py` | __main__ guard | — | 0 |
| `_v179_champions_vs_liga.py` | __main__ guard | — | 74 |
| `_v180_mapa_equipo_liga.py` | __main__ guard | — | 0 |
| `_v181_impacto_cuotas.py` | __main__ guard | — | 177 |
| `_v182_factor_competicion.py` | __main__ guard | — | 74 |
| `_v182_impacto_enchufe.py` | __main__ guard | — | 74 |
| `_v182_mide_mezcla.py` | __main__ guard | — | 74 |
| `_v184_mide_agrupado.py` | __main__ guard | — | 75 |
| `_v184_mide_agrupado_bien.py` | __main__ guard | — | 75 |
| `_v187_liquida_snapshots.py` | __main__ guard | — | 74 |
| `_v189_mide_ledger.py` | __main__ guard | — | 77 |
| `_v189_snapshot_como_cierre.py` | __main__ guard | — | 0 |
| `_v190_mide_cuotas_espn.py` | __main__ guard | — | 2 |
| `_v191_backfill_td.py` | __main__ guard | — | 26 |
| `_v191_mide_td.py` | __main__ guard | — | 29 |
| `_v192_mide_casas_mx.py` | __main__ guard | — | 0 |
| `_v227_agrupado_solo_huecos.py` | __main__ guard | — | 75 |
| `_v229_donde_vive_el_sesgo.py` | __main__ guard | — | 75 |
| `_v230_empates_correlacionados.py` | __main__ guard | — | 75 |
| `_v231_bivariada.py` | __main__ guard | — | 75 |
| `_v231_corners_tarjetas.py` | __main__ guard | — | 0 |
| `_v302_patrones_liga.py` | __main__ guard | — | 0 |
| `_v302_probables.py` | __main__ guard | — | 0 |
| `_v306_ligas_seguras.py` | __main__ guard | — | 0 |
| `_v308_bajas.py` | __main__ guard | — | 2 |
| `_v308_canal_goles.py` | __main__ guard | — | 0 |
| `_v308_fondo_fotmob.py` | __main__ guard | — | 74 |
| `_v308_reextraer_jugadores.py` | __main__ guard | — | 74 |
| `_v308_remates_jugador.py` | __main__ guard | — | 0 |
| `_v310_ajuste_conteos.py` | __main__ guard | — | 75 |
| `_v310_conteos.py` | __main__ guard | — | 74 |
| `_v310_goles.py` | __main__ guard | — | 0 |
| `_v310_peso_casa.py` | __main__ guard | — | 1 |
| `_v310_remates_cuotas.py` | __main__ guard | — | 27 |
| `_v310_replay_semana.py` | __main__ guard | — | 171 |
| `_v310_simulacion.py` | __main__ guard | — | 0 |
| `_v312_patrones.py` | __main__ guard | — | 172 |
| `_v312_resultados.py` | __main__ guard | — | 0 |
| `_v313_corners_total.py` | __main__ guard | — | 74 |
| `_v313_sin_modelo.py` | __main__ guard | — | 171 |
| `_v314_ligas_chicas.py` | __main__ guard | — | 172 |
| `_v315_modelo_competiciones.py` | __main__ guard | — | 173 |
| `_v315_rojos.py` | __main__ guard | — | 171 |
| `_v316_contexto.py` | __main__ guard | — | 1 |
| `_v316_corners_tabla.py` | __main__ guard | — | 74 |
| `_v316_meter_goles.py` | __main__ guard | — | 74 |
| `_v316_mitades.py` | __main__ guard | — | 172 |
| `_v316_modelo_flashscore.py` | __main__ guard | — | 174 |
| `_v316_patrones_extra.py` | __main__ guard | — | 75 |
| `_v316_tabla_mercados.py` | __main__ guard | — | 74 |
| `_v317_capa1.py` | __main__ guard | — | 0 |
| `_v319_conteos_reales.py` | __main__ guard | — | 74 |
| `_v320_corners_favorito.py` | __main__ guard | — | 0 |
| `_v320_selecciones.py` | __main__ guard | — | 172 |
| `_v321_corners_margen.py` | __main__ guard | — | 74 |
| `_v324_nada.py` | __main__ guard | — | 172 |
| `_v325_nfl.py` | __main__ guard | — | 29 |
| `_v326_patrones.py` | __main__ guard | — | 0 |
| `_v330_nba.py` | __main__ guard | — | 2 |
| `_v331_desacuerdo_casa.py` | __main__ guard | — | 0 |
| `_v331_encima_regla.py` | __main__ guard | — | 0 |
| `_v331_hipotesis.py` | __main__ guard | — | 0 |
| `_v331_linea_25.py` | __main__ guard | — | 0 |
| `_v331_memoria_equipos.py` | __main__ guard | — | 0 |
| `_v331_meta_ablacion.py` | __main__ guard | — | 0 |
| `_v331_rojos_app.py` | __main__ guard | — | 183 |
| `_v332_combinadas.py` | __main__ guard | — | 0 |
| `_v332_cruce_descanso.py` | __main__ guard | — | 0 |
| `_v332_novibet_real.py` | __main__ guard | — | 0 |
| `_v332_pago_anticipado.py` | __main__ guard | — | 0 |
| `_v333_constructor.py` | __main__ guard | — | 2 |
| `_v333_motor.py` | __main__ guard | — | 1 |
| `_v333_novibet_interno.py` | __main__ guard | — | 2 |
| `_v333_playdoit_pinnacle.py` | __main__ guard | — | 0 |
| `_v334_avanzado.py` | __main__ guard | — | 1 |
| `_v335_compara.py` | __main__ guard | — | 0 |
| `_v335_meter_casa.py` | __main__ guard | — | 0 |
| `_v336_bajas_mercado.py` | __main__ guard | — | 5 |
| `_v337_ligas.py` | __main__ guard | — | 1 |
| `_v342_fotos.py` | __main__ guard | — | 184 |
| `_v342_tenis.py` | __main__ guard | — | 2 |
| `_v343_estabilidad.py` | __main__ guard | — | 171 |
| `_v344_patrones.py` | __main__ guard | — | 28 |
| `_v344_precio.py` | __main__ guard | — | 27 |
| `_v344_tiros.py` | __main__ guard | — | 0 |
| `_v345_tiros.py` | __main__ guard | — | 29 |
| `_v346_fijada.py` | __main__ guard | — | 172 |
| `_v346_tiros_meter.py` | __main__ guard | — | 30 |
| `_v348_btts.py` | __main__ guard | — | 31 |
| `_v348_cambios.py` | __main__ guard | — | 173 |
| `_v349_movimiento.py` | __main__ guard | — | 28 |
| `_v350_escaleras.py` | __main__ guard | — | 0 |
| `_v350_escaleras_reales.py` | __main__ guard | — | 171 |
| `_v350_ganador.py` | __main__ guard | — | 34 |
| `_v350_totales.py` | __main__ guard | — | 33 |
| `_v351_hora.py` | __main__ guard | — | 173 |
| `_v351_semilla_capa1.py` | __main__ guard | — | 172 |
| `_v352_fijar.py` | __main__ guard | — | 173 |
| `_v354_nba_espn.py` | __main__ guard | — | 0 |
| `_v354_nba_lineas.py` | __main__ guard | — | 3 |
| `_v355_mlb_cierres.py` | __main__ guard | — | 29 |
| `_v355_mlb_medir.py` | __main__ guard | — | 0 |
| `_v356_anticipar.py` | __main__ guard | — | 0 |
| `_v356_h2h.py` | __main__ guard | — | 29 |
| `_v356_lambdas.py` | __main__ guard | — | 0 |
| `_v357_antes_despues.py` | __main__ guard | — | 1 |
| `_v357_patrones.py` | __main__ guard | — | 174 |
| `_v358_nfl_espn.py` | __main__ guard | — | 0 |
| `_v358_nfl_lineas.py` | __main__ guard | — | 30 |
| `_v358_nfl_variantes.py` | __main__ guard | — | 32 |
| `_v359_nhl_datos.py` | __main__ guard | — | 0 |
| `_v359_nhl_medir.py` | __main__ guard | — | 0 |
| `_v360_elige.py` | __main__ guard | — | 0 |
| `_v360_estrategias.py` | __main__ guard | — | 0 |
| `_v360_retiradas.py` | __main__ guard | — | 172 |
| `_v361_lineas_hist.py` | __main__ guard | — | 29 |
| `_v361_metodo.py` | __main__ guard | — | 28 |
| `_v362_corners.py` | __main__ guard | — | 29 |
| `_v362b_escaleras.py` | __main__ guard | — | 31 |
| `_v363_simulaciones.py` | __main__ guard | — | 0 |
| `_v364_btts.py` | __main__ guard | — | 31 |
| `_v364_capa1_forma.py` | __main__ guard | — | 29 |
| `_v366_rojas_arriesgadas.py` | __main__ guard | — | 0 |
| `_v368_aprendiz.py` | __main__ guard | — | 0 |
| `_v370_boleto_largo.py` | __main__ guard | — | 171 |
| `_v371_sencillas.py` | __main__ guard | — | 0 |
| `_v371b_ganador.py` | __main__ guard | — | 0 |
| `_v371c_refinar.py` | __main__ guard | — | 0 |
| `_v373_aprendiz.py` | __main__ guard | — | 28 |
| `_v373_aprendiz_revision.py` | __main__ guard | — | 0 |
| `_v373_boleto.py` | __main__ guard | — | 0 |
| `_v373_boleto_revision.py` | __main__ guard | — | 0 |
| `_v373_calibracion.py` | __main__ guard | — | 0 |
| `_v373_calibracion_revision.py` | __main__ guard | — | 0 |
| `_v373_casas.py` | __main__ guard | — | 26 |
| `_v373_contexto.py` | __main__ guard | — | 0 |
| `_v373_contexto_revision.py` | __main__ guard | — | 4 |
| `_v373_metodo_equipo.py` | __main__ guard | — | 28 |
| `_v373_metodo_equipo_revision.py` | __main__ guard | — | 0 |
| `_v373_pisos.py` | __main__ guard | — | 0 |
| `_v376_porteros.py` | __main__ guard | — | 0 |
| `_v90_auditoria_ledger.py` | __main__ guard | — | 0 |
| `_v90_edge_mezcla.py` | __main__ guard | — | 0 |
| `_v90_line_shopping_por_lado.py` | __main__ guard | — | 0 |
| `_v90_modelo_como_filtro.py` | __main__ guard | — | 0 |
| `_v90_sesgo_favorito.py` | __main__ guard | — | 0 |
| `_v90_stacking.py` | __main__ guard | — | 0 |
| `_v90_w_verano.py` | __main__ guard | — | 0 |
| `_v94_w_tenis.py` | __main__ guard | — | 0 |
| `_v97_familias_kbo.py` | __main__ guard | — | 31 |
| `_v97_familias_leagues_cup.py` | __main__ guard | — | 74 |
| `_v97_wf_kbo.py` | __main__ guard | — | 31 |
| `_v97_wf_leagues_cup.py` | __main__ guard | — | 74 |
| `_v98_backtest_kbo.py` | __main__ guard | — | 31 |
| `_v98_dos_etapas_leagues_cup.py` | __main__ guard | — | 74 |
| `_v991_ab_idf_kbo.py` | __main__ guard | — | 35 |
| `_v991_ab_idf_tenis.py` | __main__ guard | — | 32 |
| `_v992_ab_idf_mlb.py` | __main__ guard | — | 27 |
| `_v992_ab_idf_motor_tenis.py` | __main__ guard | — | 31 |
| `_v99_alternativas_kbo.py` | __main__ guard | — | 32 |
| `_v99_edge_tenis.py` | __main__ guard | — | 30 |
| `actualizar_selecciones.py` | workflow | `.github/workflows/precalculo_dia.yml` | 130 |
| `acumular_itf.py` | workflow | `.github/workflows/precalculo_dia.yml` | 1 |
| `acumular_tenis.py` | __main__ guard | — | 27 |
| `ajuste_contexto.py` | __main__ guard | — | 136 |
| `alias_equipos.py` | __main__ guard | — | 26 |
| `alias_nombres.py` | __main__ guard | — | 0 |
| `alineacion_vorp.py` | __main__ guard | — | 1 |
| `alpha_finder.py` | __main__ guard | — | 129 |
| `anclas.py` | workflow | `.github/workflows/cuotas_mx.yml` | 26 |
| `anclas_backfill.py` | __main__ guard | — | 27 |
| `anulacion_tactica.py` | __main__ guard | — | 6 |
| `api_football_manager.py` | __main__ guard | — | 0 |
| `aprendizaje_continuo.py` | __main__ guard | — | 1 |
| `arbitro_partido.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `archivo_contexto.py` | __main__ guard | — | 136 |
| `auditar_repo.py` | __main__ guard | — | 0 |
| `auditoria_ligas.py` | __main__ guard | — | 75 |
| `auditoria_pick.py` | __main__ guard | — | 133 |
| `autopsia.py` | __main__ guard | — | 3 |
| `avisos_renovacion.py` | __main__ guard | — | 0 |
| `backfill_betexplorer.py` | __main__ guard | — | 8 |
| `backfill_mlb_odds.py` | __main__ guard | — | 28 |
| `backfill_stats.py` | __main__ guard | — | 5 |
| `backtest_btts.py` | __main__ guard | — | 9 |
| `backtest_thresholds.py` | __main__ guard | — | 7 |
| `backtest_v212.py` | __main__ guard | — | 138 |
| `bajas_fotmob.py` | workflow | `.github/workflows/precalculo_dia.yml` | 76 |
| `bankroll_manager.py` | __main__ guard | — | 0 |
| `barrido_capa1.py` | workflow | `.github/workflows/cuotas_mx.yml` | 26 |
| `barrido_ligas.py` | __main__ guard | — | 0 |
| `betexplorer_scraper.py` | __main__ guard | — | 26 |
| `bot_dia_completo.py` | workflow | `.github/workflows/telegram_dia_completo.yml` | 183 |
| `bot_telegram.py` | workflow | `.github/workflows/telegram_bot.yml` | 183 |
| `build_ledger_deportes.py` | __main__ guard | — | 40 |
| `build_ledger_handicap.py` | __main__ guard | — | 1 |
| `build_ledger_total.py` | __main__ guard | — | 0 |
| `build_ledger_totales.py` | __main__ guard | — | 74 |
| `build_pick_ledger.py` | __main__ guard | — | 76 |
| `buscador_fuentes.py` | __main__ guard | — | 1 |
| `calibracion_confianza.py` | __main__ guard | — | 2 |
| `calibracion_elo.py` | __main__ guard | — | 0 |
| `calibracion_mercado.py` | __main__ guard | — | 0 |
| `calibrador_bandas.py` | __main__ guard | — | 1 |
| `calibrador_btts.py` | __main__ guard | — | 0 |
| `calibrador_goles.py` | __main__ guard | — | 74 |
| `calibrar_contexto_nfl.py` | __main__ guard | — | 29 |
| `catalogo_equipos.py` | __main__ guard | — | 7 |
| `clima.py` | __main__ guard | — | 0 |
| `clv_tracker.py` | __main__ guard | — | 0 |
| `comentarios_correo.py` | __main__ guard | — | 0 |
| `confianza_mercado.py` | __main__ guard | — | 0 |
| `contexto_ponches.py` | __main__ guard | — | 0 |
| `contexto_previo.py` | __main__ guard | — | 0 |
| `corners_fotmob.py` | __main__ guard | — | 74 |
| `corners_tabla.py` | __main__ guard | — | 74 |
| `cuotas_manual.py` | __main__ guard | — | 0 |
| `cuotas_multi.py` | __main__ guard | — | 26 |
| `cuotas_mx.py` | workflow | `.github/workflows/cuotas_mx.yml` | 26 |
| `daily_snapshots.py` | __main__ guard | — | 80 |
| `data_fetcher.py` | __main__ guard | — | 7 |
| `data_health.py` | __main__ guard | — | 26 |
| `decisiones_dia.py` | __main__ guard | — | 171 |
| `edge_engine.py` | __main__ guard | — | 4 |
| `elo_global.py` | __main__ guard | — | 0 |
| `engines/kbo_engine.py` | __main__ guard | — | 31 |
| `engines/mlb_engine.py` | __main__ guard | — | 26 |
| `engines/nba_engine.py` | __main__ guard | — | 7 |
| `engines/tennis_engine.py` | __main__ guard | — | 30 |
| `entrenar_ligas_v68.py` | __main__ guard | — | 74 |
| `escalada_lineas.py` | __main__ guard | — | 0 |
| `espn_extras.py` | workflow | `.github/workflows/precalcular_rosters.yml`, `.github/workflows/retrain_leagues.yml` | 26 |
| `exportar_web.py` | __main__ guard | — | 185 |
| `fbref_league_scraper.py` | __main__ guard | — | 5 |
| `fbref_scraper_v3.py` | __main__ guard | — | 0 |
| `feedback_humano.py` | __main__ guard | — | 171 |
| `fiabilidad_picks.py` | __main__ guard | — | 171 |
| `fixtures_espn.py` | __main__ guard | — | 26 |
| `forma_equipos.py` | __main__ guard | — | 0 |
| `fotmob_ligas.py` | __main__ guard | — | 7 |
| `fotmob_scraper.py` | __main__ guard | — | 0 |
| `frescura_datos.py` | workflow | `.github/workflows/recalibrar.yml` | 26 |
| `fuente_bajas.py` | __main__ guard | — | 136 |
| `generar_ligas_v68.py` | __main__ guard | — | 1 |
| `generar_universo_selecciones.py` | __main__ guard | — | 4 |
| `git_sin_conflictos.py` | workflow | `.github/workflows/precalculo_dia.yml`, `.github/workflows/retrain_leagues.yml` | 0 |
| `goleadores.py` | __main__ guard | — | 74 |
| `historico_fotmob.py` | workflow | `.github/workflows/precalculo_dia.yml` | 28 |
| `historico_selecciones.py` | workflow | `.github/workflows/precalculo_dia.yml` | 27 |
| `ia_gemini.py` | __main__ guard | — | 182 |
| `import_historical_odds.py` | workflow | `.github/workflows/recalibrar.yml` | 6 |
| `indice_forma.py` | __main__ guard | — | 0 |
| `informe_calibracion.py` | workflow | `.github/workflows/recalibrar.yml` | 74 |
| `ingesta_cuotas_kbo.py` | __main__ guard | — | 0 |
| `ingesta_cuotas_leagues_cup.py` | __main__ guard | — | 74 |
| `ingesta_itf.py` | __main__ guard | — | 0 |
| `jugadores_prob.py` | __main__ guard | — | 182 |
| `kbo_naver.py` | __main__ guard | — | 0 |
| `kbo_preview.py` | __main__ guard | — | 2 |
| `kelly_simultaneo.py` | __main__ guard | — | 1 |
| `league_engine.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `leagues_cup.py` | __main__ guard | — | 74 |
| `lineas_jugador.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `lineup_collector.py` | __main__ guard | — | 0 |
| `lineup_impact.py` | __main__ guard | — | 1 |
| `liquidador.py` | __main__ guard | — | 31 |
| `liquidador_ponches.py` | __main__ guard | — | 2 |
| `liquidar_pendientes.py` | __main__ guard | — | 182 |
| `live_worldcup.py` | __main__ guard | — | 9 |
| `memoria_equipos.py` | __main__ guard | — | 26 |
| `mercado_estabilidad.py` | __main__ guard | — | 1 |
| `mercado_implicito.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `mlb_statsapi.py` | __main__ guard | — | 26 |
| `mls_features.py` | __main__ guard | — | 1 |
| `model_audit.py` | __main__ guard | — | 4 |
| `modelo_nfl.py` | __main__ guard | — | 28 |
| `modo_seguridad.py` | __main__ guard | — | 136 |
| `monitor_canales.py` | __main__ guard | — | 0 |
| `monitor_playdoit.py` | __main__ guard | — | 74 |
| `motor_goles.py` | __main__ guard | — | 29 |
| `name_mapper.py` | __main__ guard | — | 1 |
| `nba_features.py` | __main__ guard | — | 0 |
| `nba_historico.py` | workflow | `.github/workflows/retrain_leagues.yml` | 0 |
| `nba_scraper.py` | __main__ guard | — | 0 |
| `nfl_datos.py` | __main__ guard | — | 26 |
| `nfl_lineshop.py` | __main__ guard | — | 26 |
| `nfl_nflverse.py` | workflow | `.github/workflows/precalculo_dia.yml` | 0 |
| `odds_store.py` | __main__ guard | — | 6 |
| `patas_veredicto.py` | __main__ guard | — | 178 |
| `patrones_acierto.py` | __main__ guard | — | 0 |
| `patrones_liga.py` | __main__ guard | — | 74 |
| `pipeline_mundial.py` | __main__ guard | — | 17 |
| `pipeline_total.py` | workflow | `.github/workflows/telegram_bot.yml`, `.github/workflows/telegram_dia_completo.yml` | 82 |
| `player_db.py` | __main__ guard | — | 0 |
| `portfolio_optimizer.py` | __main__ guard | — | 131 |
| `precalcular_goleadores.py` | __main__ guard | — | 74 |
| `precalculo_dia.py` | __main__ guard | — | 175 |
| `precision_ligas.py` | __main__ guard | — | 1 |
| `predicciones_dia.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `prediction_api.py` | __main__ guard | — | 13 |
| `pronosticos_guardados.py` | __main__ guard | — | 171 |
| `props_model.py` | __main__ guard | — | 0 |
| `publicar_modelos.py` | __main__ guard | — | 2 |
| `pulso_historial.py` | __main__ guard | — | 0 |
| `radar_capturas.py` | __main__ guard | — | 0 |
| `radar_errores.py` | workflow | `.github/workflows/radar_diario.yml` | 1 |
| `recalibrar_todo.py` | __main__ guard | — | 184 |
| `recalibrate_from_history.py` | workflow | `.github/workflows/retrain_leagues.yml` | 1 |
| `referee_scraper.py` | __main__ guard | — | 1 |
| `remates_flashscore.py` | workflow | `.github/workflows/precalculo_dia.yml` | 74 |
| `remates_fotmob.py` | workflow | `.github/workflows/precalculo_dia.yml` | 74 |
| `remates_jugador.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `remates_jugadores.py` | __main__ guard | — | 26 |
| `remates_ml.py` | __main__ guard | — | 74 |
| `rendimiento_real.py` | __main__ guard | — | 1 |
| `respaldo_base.py` | __main__ guard | — | 0 |
| `resultados_flashscore.py` | __main__ guard | — | 1 |
| `resultados_fotmob.py` | __main__ guard | — | 136 |
| `resumen_mensual.py` | __main__ guard | — | 0 |
| `retrosheet_scraper.py` | __main__ guard | — | 0 |
| `riesgo_liga.py` | __main__ guard | — | 0 |
| `scraper_contexto.py` | __main__ guard | — | 136 |
| `selector_apuestas.py` | __main__ guard | — | 172 |
| `semaforo_capa1.py` | __main__ guard | — | 0 |
| `senal_bajas.py` | __main__ guard | — | 0 |
| `sgp_correlation.py` | __main__ guard | — | 4 |
| `shadow_booster.py` | __main__ guard | — | 74 |
| `simular_sonadora.py` | __main__ guard | — | 0 |
| `snapshots_corners.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `snapshots_remates.py` | workflow | `.github/workflows/retrain_leagues.yml` | 76 |
| `snapshots_tarjetas.py` | workflow | `.github/workflows/retrain_leagues.yml` | 75 |
| `sondeo_casas.py` | __main__ guard | — | 0 |
| `sondeo_odds_api.py` | __main__ guard | — | 0 |
| `source_resilience.py` | __main__ guard | — | 1 |
| `stats_espn.py` | workflow | `.github/workflows/recalibrar.yml`, `.github/workflows/retrain_leagues.yml` | 26 |
| `stats_estimadas.py` | workflow | `.github/workflows/recalibrar.yml` | 74 |
| `stats_flashscore.py` | workflow | `.github/workflows/retrain_leagues.yml` | 75 |
| `stats_fotmob.py` | workflow | `.github/workflows/retrain_leagues.yml` | 74 |
| `statsbomb_calibration.py` | __main__ guard | — | 0 |
| `supervivencia_btts.py` | __main__ guard | — | 0 |
| `tarjeta_tg.py` | __main__ guard | — | 0 |
| `telegram_canales.py` | __main__ guard | — | 184 |
| `tenis_fuentes.py` | __main__ guard | — | 29 |
| `tenis_juegos.py` | __main__ guard | — | 30 |
| `tenis_saque.py` | __main__ guard | — | 30 |
| `test_anclas.py` | __main__ guard | — | 27 |
| `test_bajas.py` | __main__ guard | — | 76 |
| `test_catalogo_y_cuotas.py` | __main__ guard | — | 229 |
| `test_combinada.py` | __main__ guard | — | 30 |
| `test_concurrencia.py` | __main__ guard | — | 177 |
| `test_dia_picks.py` | __main__ guard | — | 2 |
| `test_escalera.py` | __main__ guard | — | 2 |
| `test_exportador_web_v402.py` | workflow | `.github/workflows/sitio_web.yml`, `.github/workflows/validate_sharpicks.yml` | 186 |
| `test_forma.py` | __main__ guard | — | 3 |
| `test_jugados_del_dia.py` | __main__ guard | — | 171 |
| `test_ligas_sin_motor.py` | __main__ guard | — | 171 |
| `test_match_parlay.py` | __main__ guard | — | 77 |
| `test_mercados_equipo.py` | __main__ guard | — | 171 |
| `test_patrones_liga.py` | __main__ guard | — | 74 |
| `test_probables.py` | __main__ guard | — | 30 |
| `test_radar.py` | __main__ guard | — | 26 |
| `test_recarga.py` | __main__ guard | — | 1 |
| `test_relevo.py` | __main__ guard | — | 0 |
| `test_remates_fotmob.py` | __main__ guard | — | 77 |
| `test_selecciones.py` | __main__ guard | — | 130 |
| `test_semaforo.py` | __main__ guard | — | 1 |
| `test_simetria.py` | __main__ guard | — | 14 |
| `test_v308.py` | __main__ guard | — | 173 |
| `test_v309.py` | __main__ guard | — | 171 |
| `test_v310.py` | __main__ guard | — | 171 |
| `test_v311.py` | __main__ guard | — | 171 |
| `test_v312.py` | __main__ guard | — | 184 |
| `test_v313.py` | __main__ guard | — | 183 |
| `test_v314.py` | __main__ guard | — | 183 |
| `test_v315.py` | __main__ guard | — | 172 |
| `test_v316.py` | __main__ guard | — | 171 |
| `test_v317.py` | __main__ guard | — | 183 |
| `test_v318.py` | __main__ guard | — | 183 |
| `test_v319.py` | __main__ guard | — | 183 |
| `test_v320.py` | __main__ guard | — | 171 |
| `test_v321.py` | __main__ guard | — | 171 |
| `test_v323.py` | __main__ guard | — | 173 |
| `test_v324.py` | __main__ guard | — | 171 |
| `test_v325.py` | __main__ guard | — | 171 |
| `test_v326.py` | __main__ guard | — | 74 |
| `test_v327.py` | __main__ guard | — | 171 |
| `test_v328.py` | __main__ guard | — | 171 |
| `test_v329.py` | __main__ guard | — | 171 |
| `test_v330.py` | __main__ guard | — | 171 |
| `test_v331.py` | __main__ guard | — | 171 |
| `test_v333.py` | __main__ guard | — | 1 |
| `test_v335.py` | __main__ guard | — | 171 |
| `test_v337.py` | __main__ guard | — | 1 |
| `test_v338.py` | __main__ guard | — | 1 |
| `test_v339.py` | __main__ guard | — | 1 |
| `test_v340.py` | __main__ guard | — | 194 |
| `test_v342.py` | __main__ guard | — | 177 |
| `test_v343.py` | __main__ guard | — | 194 |
| `test_v345.py` | __main__ guard | — | 171 |
| `test_v346.py` | __main__ guard | — | 174 |
| `test_v347.py` | __main__ guard | — | 171 |
| `test_v348.py` | __main__ guard | — | 172 |
| `test_v350.py` | __main__ guard | — | 174 |
| `test_v351.py` | __main__ guard | — | 174 |
| `test_v352.py` | __main__ guard | — | 171 |
| `test_v353.py` | __main__ guard | — | 171 |
| `test_v354.py` | __main__ guard | — | 172 |
| `test_v355.py` | __main__ guard | — | 171 |
| `test_v356.py` | __main__ guard | — | 171 |
| `test_v358.py` | __main__ guard | — | 171 |
| `test_v359.py` | __main__ guard | — | 171 |
| `test_v360.py` | __main__ guard | — | 171 |
| `test_v361.py` | __main__ guard | — | 171 |
| `test_v362.py` | __main__ guard | — | 172 |
| `test_v363.py` | __main__ guard | — | 174 |
| `test_v364.py` | __main__ guard | — | 172 |
| `test_v365.py` | __main__ guard | — | 171 |
| `test_v366.py` | __main__ guard | — | 173 |
| `test_v367.py` | __main__ guard | — | 171 |
| `test_v368.py` | __main__ guard | — | 171 |
| `test_v369.py` | __main__ guard | — | 183 |
| `test_v370.py` | __main__ guard | — | 184 |
| `test_v371.py` | __main__ guard | — | 195 |
| `test_v372.py` | __main__ guard | — | 172 |
| `test_v373.py` | __main__ guard | — | 174 |
| `test_v374.py` | __main__ guard | — | 183 |
| `test_v375.py` | __main__ guard | — | 171 |
| `test_v377.py` | __main__ guard | — | 186 |
| `test_v378.py` | __main__ guard | — | 186 |
| `test_v379.py` | workflow | `.github/workflows/sitio_web.yml` | 195 |
| `test_v381.py` | __main__ guard | — | 185 |
| `test_v383.py` | workflow | `.github/workflows/validate_sharpicks.yml` | 0 |
| `test_v384.py` | __main__ guard | — | 195 |
| `test_v386.py` | __main__ guard | — | 182 |
| `test_v389.py` | workflow | `.github/workflows/sitio_web.yml`, `.github/workflows/test_sharpicks_v402.yml`, `.github/workflows/validate_sharpicks.yml` | 186 |
| `test_v390.py` | workflow | `.github/workflows/validate_sharpicks.yml` | 0 |
| `test_v392.py` | __main__ guard | — | 74 |
| `test_v393.py` | __main__ guard | — | 75 |
| `test_v394.py` | workflow | `.github/workflows/validate_sharpicks.yml` | 182 |
| `test_v395.py` | workflow | `.github/workflows/validate_sharpicks.yml` | 3 |
| `test_v396.py` | workflow | `.github/workflows/validate_sharpicks.yml` | 183 |
| `test_v400.py` | workflow | `.github/workflows/sitio_web.yml`, `.github/workflows/test_sharpicks_v402.yml`, `.github/workflows/validate_sharpicks.yml` | 192 |
| `test_v406.py` | __main__ guard | — | 186 |
| `test_v413.py` | __main__ guard | — | 0 |
| `test_v415.py` | __main__ guard | — | 182 |
| `test_v417.py` | __main__ guard | — | 188 |
| `test_v446.py` | __main__ guard | — | 182 |
| `test_v463.py` | __main__ guard | — | 182 |
| `test_v466.py` | __main__ guard | — | 186 |
| `test_v467.py` | __main__ guard | — | 182 |
| `test_v468.py` | __main__ guard | — | 0 |
| `test_v469.py` | __main__ guard | — | 183 |
| `test_v470.py` | __main__ guard | — | 1 |
| `test_v477.py` | __main__ guard | — | 182 |
| `test_v478.py` | __main__ guard | — | 186 |
| `test_v479.py` | __main__ guard | — | 186 |
| `test_v480.py` | __main__ guard | — | 186 |
| `test_v481.py` | __main__ guard | — | 182 |
| `test_v482.py` | __main__ guard | — | 186 |
| `test_v483.py` | __main__ guard | — | 8 |
| `test_v484.py` | __main__ guard | — | 0 |
| `test_v486.py` | __main__ guard | — | 0 |
| `test_v491.py` | __main__ guard | — | 186 |
| `test_v492.py` | __main__ guard | — | 183 |
| `test_v494.py` | __main__ guard | — | 0 |
| `test_v497.py` | __main__ guard | — | 1 |
| `test_v499.py` | __main__ guard | — | 0 |
| `test_v502.py` | __main__ guard | — | 186 |
| `test_v503.py` | __main__ guard | — | 0 |
| `test_v505.py` | __main__ guard | — | 186 |
| `test_v506.py` | __main__ guard | — | 171 |
| `test_v508.py` | __main__ guard | — | 186 |
| `test_v510.py` | __main__ guard | — | 186 |
| `test_v512.py` | __main__ guard | — | 0 |
| `test_v513.py` | __main__ guard | — | 1 |
| `test_v519.py` | __main__ guard | — | 0 |
| `test_v520.py` | __main__ guard | — | 1 |
| `test_v527.py` | __main__ guard | — | 185 |
| `test_v528.py` | __main__ guard | — | 1 |
| `test_v531.py` | __main__ guard | — | 0 |
| `test_v544.py` | __main__ guard | — | 195 |
| `test_vistas_compactas.py` | __main__ guard | — | 5 |
| `tests/test_python_dependency_graph.py` | __main__ guard | — | 1 |
| `tests/test_sharpicks_contracts.py` | __main__ guard | — | 2 |
| `tiros_equipo.py` | __main__ guard | — | 27 |
| `tiros_seguimiento.py` | __main__ guard | — | 76 |
| `tools/python_dependency_graph.py` | __main__ guard | — | 0 |
| `train_tda_model.py` | __main__ guard | — | 7 |
| `transfermarkt_scraper.py` | __main__ guard | — | 0 |
| `uefa_scraper.py` | __main__ guard | — | 7 |
| `update_team_stats.py` | __main__ guard | — | 6 |
| `valida_render.py` | __main__ guard | — | 0 |
| `validacion_deportes.py` | __main__ guard | — | 129 |
| `validar_contexto.py` | __main__ guard | — | 0 |
| `validar_riesgo.py` | __main__ guard | — | 3 |
| `validar_sonadora.py` | __main__ guard | — | 1 |
| `valor_en_vivo.py` | __main__ guard | — | 76 |
| `veredicto_pick.py` | __main__ guard | — | 171 |
| `vigia_limites.py` | __main__ guard | — | 0 |

El conteo de `__main__ guard` incluye scripts históricos, pruebas y herramientas de análisis; no significa que todos estén activos en producción. Los 44 scripts de workflows son los comandos literales que el analizador pudo asociar a los 18 YAML.

## Módulos con mayor cantidad de importadores

| Módulo | Importadores locales |
|---|---:|
| `config` | 87 |
| `modo_modelo` | 68 |
| `cuotas_multi` | 66 |
| `rendimiento_equipos` | 61 |
| `fixtures_espn` | 60 |
| `name_mapper` | 52 |
| `horario` | 41 |
| `partidos_jugados` | 36 |
| `pronosticos_guardados` | 33 |
| `league_engine` | 31 |
| `veredicto_pick` | 29 |
| `io_atomico` | 24 |
| `mercado_implicito` | 22 |
| `alpha_finder` | 20 |
| `tiros_equipo` | 20 |
| `exportar_web` | 19 |
| `decisiones_dia` | 17 |
| `dia_picks` | 16 |
| `mercado_sin_modelo` | 16 |
| `remates_fotmob` | 14 |

## Raíces de imports que no resuelven a archivo local

| Raíz | Referencias |
|---|---:|
| `pandas` | 560 |
| `json` | 544 |
| `os` | 463 |
| `sys` | 398 |
| `numpy` | 379 |
| `logging` | 327 |
| `typing` | 288 |
| `datetime` | 182 |
| `io` | 172 |
| `sklearn` | 159 |
| `__future__` | 158 |
| `time` | 155 |
| `requests` | 148 |
| `re` | 126 |
| `argparse` | 74 |
| `warnings` | 70 |
| `tempfile` | 68 |
| `scipy` | 67 |
| `math` | 64 |
| `glob` | 51 |
| `unicodedata` | 49 |
| `lightgbm` | 48 |
| `collections` | 44 |
| `subprocess` | 42 |
| `inspect` | 39 |
| `concurrent` | 37 |
| `importlib` | 32 |
| `difflib` | 26 |
| `ast` | 23 |
| `csv` | 19 |

## Componentes cíclicos

- `alias_equipos`, `cuotas_multi`, `cuotas_mx`, `engines.mlb_engine`, `fixtures_espn`, `mlb_statsapi`, `nfl_datos`
- `alpha_finder`, `selecciones_dia`, `validacion_deportes`
- `analisis_seguimiento`, `anunciadas`, `decisiones_dia`, `fiabilidad_picks`, `lo_mejor`, `mercado_sin_modelo`, `modelo_competiciones`, `modo_modelo`, `partidos_jugados`, `pata_h2h`, `pata_historica`, `pronosticos_guardados`, `tabla_liga`, `valor_apuesta`, `veredicto_pick`
- `arbitro_partido`, `calibrador_lambda`, `cdi_futbol`, `corners_fotmob`, `corners_tabla`, `goleadores`, `historico_real`, `league_engine`, `leagues_cup`, `lineas_jugador`, `patrones_liga`, `perfil_liga_local`, `remates_fotmob`, `remates_jugador`, `remates_ml`, `rendimiento_equipos`, `stats_estimadas`
- `bajas_fotmob`, `bajas_modelo`
- `bot_telegram`, `formato_ia`
- `engines.kbo_engine`
- `engines.nba_engine`
- `errores_web`, `escudos`, `ia_gemini`, `liquidar_pendientes`
- `fuente_bajas`, `scraper_contexto`
- `import_historical_odds`, `odds_store`

## Limitaciones

- Un import no resuelto puede ser biblioteca estándar, dependencia de terceros, import relativo especial, paquete namespace o dependencia opcional; no se etiqueta automáticamente como error.
- Imports dinámicos con valor calculado, plugins, rutas por configuración y ejecución shell sólo quedan marcados, no resueltos transitivamente.
- Referencias de archivo son strings literales/calls conocidos; no demuestran I/O real ni distinguen con certeza datos de rutas de URL/identificadores.
- Llamadas top-level son candidatas observadas sintácticamente; no prueban que el módulo se importe ni el efecto externo exacto.
- Los entrypoints por workflow se detectan para comandos `python <archivo.py>` literales; comandos construidos, módulos `-m` y scripts descargados requieren revisión adicional.
- No se ejecutó ningún módulo de SharPicks ni se contactaron servicios.

El detalle reproducible por módulo, líneas, aristas y sitios pendientes está en `python_dependency_graph.json`.
Reproducir con `python tools/python_dependency_graph.py --json docs/auditoria/python_dependency_graph.json --markdown docs/auditoria/01_GRAFO_ARQUITECTURA.md`.
