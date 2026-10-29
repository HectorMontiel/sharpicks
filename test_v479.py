#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v479 — DFB-Pokal y Copa del Rey dentro del modelo y de las apuestas, con la metodología de las copas
(la liga de cada equipo, v415), y las copas liquidadas A LOS 90': ESPN y FotMob dan el final con prórroga
y la casa paga el 1X2 y los totales en tiempo regular. Sin red."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar_alta():
    import config
    import config_ligas_espn as cl
    import fixtures_espn as fx
    import catalogo_equipos as ce
    for clave, code in (('ger_dfb_pokal', 'ger.dfb_pokal'), ('esp_copa_rey', 'esp.copa_del_rey')):
        cfg = config.LEAGUES.get(clave) or {}
        check(cfg.get('disponible') and cfg.get('formato') == 'espn' and fx.ESPN_CODIGOS.get(clave) == code,
              'v479: %s encendida, formato espn y en ESPN_CODIGOS (%s)' % (clave, code))
        check(ce._es_copa(clave), 'v479: %s es copa (no da pertenencia: cada equipo sigue en su liga)' % clave)
    check('ger_dfb_pokal' not in cl.SIN_VOLUMEN, 'v479: la Pokal ya no está entre las descartadas por volumen')
    src = open('nombres_ligas.py', encoding='utf-8').read()
    check("'ger_dfb_pokal'" in src and 'copa de alemania' in src, 'v479: el tablero (Flashscore/Playdoit) lleva la Pokal a su clave')


def probar_90():
    import fixtures_espn as fx
    comp = [{'homeAway': 'home', 'linescores': [{'displayValue': '1'}, {'displayValue': '1'}, {'displayValue': '0'}, {'displayValue': '3'}]},
            {'homeAway': 'away', 'linescores': [{'displayValue': '0'}, {'displayValue': '2'}, {'displayValue': '0'}, {'displayValue': '0'}]}]
    check(fx.linescores_90(comp) == (2, 2), 'v479: Real Madrid 5-2 Celta (prórroga) era 2-2 a los 90\'')
    check(fx.linescores_90([{'homeAway': 'home'}, {'homeAway': 'away'}]) is None, 'v479: sin goles por parte, no se adivina')
    normal = {'id': '1', 'competitions': [{'status': {'type': {'name': 'STATUS_FULL_TIME'}}}]}
    check(fx.marcador_90('esp.copa_del_rey', normal, 3, 1) == (3, 1), 'v479: sin prórroga, el marcador de siempre (sin pedir nada)')
    fx._A_90['77'] = (1, 1)
    aet = {'id': '77', 'competitions': [{'status': {'type': {'name': 'STATUS_FINAL_AET'}}}]}
    check(fx.marcador_90('esp.copa_del_rey', aet, 2, 1) == (1, 1), 'v479: con prórroga, el de los 90\'')
    fx._A_90['78'] = None
    pen = {'id': '78', 'competitions': [{'status': {'type': {'name': 'STATUS_FINAL_PEN'}}}]}
    check(fx.marcador_90('ger.dfb_pokal', pen, 1, 1) is None, 'v479: si no se sabe el de los 90\', no se liquida')
    src = open('fixtures_espn.py', encoding='utf-8').read()
    check(src.count('marcador_90(') >= 3, 'v479: los dos lectores de resultados de ESPN pasan por marcador_90')
    lp = open('liquidar_pendientes.py', encoding='utf-8').read()
    check('fx.linescores_90(cs)' in lp and "'corners': None, 'tarjetas': None" in lp,
          'v479: liquidar_pendientes usa los 90\' y no califica córners/tarjetas de un partido con prórroga')
    pj = open('partidos_jugados.py', encoding='utf-8').read()
    check("in ('AET', 'PEN', 'AP', 'ET')" in pj, 'v479: FotMob con prórroga no pone marcador (lo da ESPN)')
    ue = open('uefa_scraper.py', encoding='utf-8').read()
    # v483: la Leagues Cup (penales sin prórroga) conserva sus empates; el resto, igual que antes
    check("if st in ('STATUS_FINAL_AET', 'STATUS_FINAL_ET') or (\n                        st == 'STATUS_FINAL_PEN' and liga_espn not in PENALES_SIN_PRORROGA):\n                    continue" in ue
          and "PENALES_SIN_PRORROGA = {'concacaf.leagues.cup', 'eng.league_cup'}" in ue,
          'v479: los partidos con prórroga no entran al entrenamiento con el marcador de la prórroga')


def probar_solo_analisis_y_agrupado():
    import config
    import exportar_web as ew
    solo = ew._ligas_solo_analisis()
    check(set(solo) >= {'ger_dfb_pokal', 'esp_copa_rey'},
          'v479: las dos copas son SÓLO ANÁLISIS hasta medirlas al nivel de las ligas: %s' % sorted(solo))
    check(not ew._cuenta({'clave_liga': 'esp_copa_rey'}, solo) and not ew._cuenta({'liga': 'DFB-Pokal'}, solo)
          and ew._cuenta({'clave_liga': 'laliga', 'liga': 'LaLiga'}, solo),
          'v479: un pick de copa no cuenta (ni por clave ni por nombre); uno de liga sí')
    src = open('exportar_web.py', encoding='utf-8').read()
    check(src.count('_cuenta(') >= 4, 'v479: fuera de próximos, jugados y errores de cuota (salen como tarjeta de análisis)')
    for clave, ligas in (('ger_dfb_pokal', ['bundesliga', 'ger_bundesliga2']), ('esp_copa_rey', ['laliga', 'esp_hypermotion'])):
        check(config.LEAGUES[clave].get('agrupar_con') == ligas, 'v479: %s se entrena con sus ligas %s (ELO común)' % (clave, ligas))
    le = open('league_engine.py', encoding='utf-8').read()
    check("if cfg.get('agrupar_con'):" in le and '_nm.mapear(n, catalogo' in le,
          'v479: el agrupado unifica los nombres de la copa con los de la liga (si no, el ELO común no une nada)')
    import pandas as pd
    h = pd.read_csv('historico_ger_dfb_pokal.csv')
    copa = h[h.competicion == 'ger_dfb_pokal']
    check({'Bayern Munich', 'Dortmund', 'Leverkusen'} <= set(copa.home_team) | set(copa.away_team)
          and {'bundesliga', 'ger_bundesliga2'} <= set(h.competicion),
          'v479: en el histórico de la Pokal, los partidos de copa usan el nombre de la liga («Dortmund»)')


if __name__ == '__main__':
    probar_alta()
    probar_90()
    probar_solo_analisis_y_agrupado()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
