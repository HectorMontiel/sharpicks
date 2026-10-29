#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v480 — KBO sin Naver (web oficial + cortacircuitos), tenis que se cierra (ficha del jugador en
Flashscore, nula sin resultado oficial, ITF acumulado en cada pasada), la sugerencia de las copas sale
de la casa y el reentrenamiento con margen. Sin red."""
import datetime as dt
import os
import sys
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar_kbo():
    import kbo_naver as k
    g = k._de_kbo_oficial({'G_ID': '20250920SSLG0', 'T_SCORE_CN': '14', 'B_SCORE_CN': '4', 'GAME_STATE_SC': '3',
                           'CANCEL_SC_ID': '0', 'T_PIT_P_NM': '원태인 ', 'B_PIT_P_NM': '톨허스트 ', 'S_NM': '잠실'})
    f = k._fila(g, solo_finalizados=True)
    check(f and f['home_team'] == 'LG Twins' and f['away_team'] == 'Samsung Lions' and f['home_runs'] == 4
          and f['away_runs'] == 14 and f['home_pitcher'] == '톨허스트',
          'v480 KBO: la web oficial con los códigos de Naver (G_ID «SSLG» = Samsung en LG; T = visita, B = local)')
    c = k._de_kbo_oficial({'G_ID': '20250920HHKT0', 'GAME_STATE_SC': '4', 'CANCEL_SC_ID': '1'})
    check(k._fila(c, solo_finalizados=False) is None, 'v480 KBO: el cancelado no entra')
    llamadas = []
    viejo_get, viejo_sleep, viejo_of = k.requests.get, k.time.sleep, k._juegos_kbo_oficial

    def falla(*a, **kw):
        llamadas.append(1)
        raise TimeoutError('sin respuesta')
    k.requests.get, k.time.sleep = falla, (lambda s: None)
    k._juegos_kbo_oficial = lambda d, h: [g]
    try:
        k._CAIDA['hasta'] = 0
        r1 = k._juegos('2025-09-20', '2025-09-20')
        n1 = len(llamadas)
        r2 = k._juegos('2025-09-20', '2025-09-20')
    finally:
        k.requests.get, k.time.sleep, k._juegos_kbo_oficial = viejo_get, viejo_sleep, viejo_of
        k._CAIDA['hasta'] = 0
    check(r1 == [g] and r2 == [g], 'v480 KBO: con Naver caído, los juegos salen de la web oficial')
    check(n1 == 2 and len(llamadas) == 2, 'v480 KBO: tras el fallo, Naver no se vuelve a pedir en 10 min (cortacircuitos)')


def probar_tenis():
    import liquidar_pendientes as lp
    check(lp._rival('Stefaniya Neporent', 'Neparent S.') and lp._rival('Faris Zakaryia', 'Zakaria F.')
          and not lp._rival('Stefaniya Neporent', 'Neparent K.') and not lp._rival('Anna Yang', 'Lin Y. J./Shao Y.'),
          'v480 tenis: el rival con otra transliteración («Neporent»/«Neparent») e inicial igual; dobles no')
    viejo = lp._palabras
    cands = [{'sport': {'id': 2}, 'type': {'name': 'Player'}, 'name': 'Fukuda Masahiro', 'url': 'fukuda-masahiro', 'id': 'x1'},
             {'sport': {'id': 2}, 'type': {'name': 'Player'}, 'name': 'Fukuda Sora', 'url': 'fukuda-sora', 'id': 'x2'}]
    ses = types.SimpleNamespace(get=lambda *a, **kw: types.SimpleNamespace(json=lambda: cands))
    lp._FICHAS.clear()
    check(lp._ficha_tenista('Sora Fukuda', ses) == ('fukuda-sora', 'x2'), 'v480 tenis: «Sora Fukuda» NO es «Fukuda Masahiro»')
    hoy = dt.datetime.now(dt.timezone.utc).date()
    d0 = hoy - dt.timedelta(days=5)
    lp._FICHAS.update({'Kamilla Bartone': ('bartone', 'b'), 'Stefaniya Neporent': ('neporent', 'n'),
                       'Theodore Dean': ('dean', 'd'), 'Adriano Dzhenev': ('dzhenev', 'z')})
    lp._PAGINAS.update({('bartone', 'b'): [{'d': d0 + dt.timedelta(days=2), 'h': 'Neparent S.', 'a': 'Bartone K.', 'gh': 0, 'ga': 2}],
                        ('neporent', 'n'): [], ('dean', 'd'): [{'d': d0 - dt.timedelta(days=20), 'h': 'Dean T.', 'a': 'Otro X.', 'gh': 2, 'ga': 0}],
                        ('dzhenev', 'z'): []})
    r = lp._tenis_por_jugador({'partido': 'Stefaniya Neporent vs Kamilla Bartone', 'fecha': d0.isoformat()}, None)
    check(r and r.get('g') == (0, 2), 'v480 tenis: sale de la ficha del jugador aunque el pick esté fechado 2 días antes: %s' % r)
    r = lp._tenis_por_jugador({'partido': 'Theodore Dean vs Adriano Dzhenev', 'fecha': d0.isoformat()}, None)
    check(r == {'nula': 'sin resultado oficial'}, 'v480 tenis: las dos fichas sin el partido → nula «sin resultado oficial»: %s' % r)
    r = lp._tenis_por_jugador({'partido': 'Theodore Dean vs Adriano Dzhenev', 'fecha': (hoy - dt.timedelta(days=1)).isoformat()}, None)
    check(r is None, 'v480 tenis: antes de 3 días no se anula')
    lp._PAGINAS[('dean', 'd')] = [{'d': d0 + dt.timedelta(days=1), 'h': 'Dean T.', 'a': 'Dzhenovski A.', 'gh': 2, 'ga': 1}]
    r = lp._tenis_por_jugador({'partido': 'Theodore Dean vs Adriano Dzhenev', 'fecha': d0.isoformat()}, None)
    check(r is None, 'v480 tenis: con un rival medio parecido en la ventana no se decide (puede ser el mismo mal escrito)')
    src = open('liquidar_pendientes.py', encoding='utf-8').read()
    check("res = {'nula': 'sin resultado oficial'}" in src and 'SIN_FUENTE_DIAS' in src and 'MAX_FICHAS' in src
          and "cerrados[p['id']] = ('nula', res['nula'])" in src,
          'v480 tenis: a los 10 días sin ninguna fuente, nula; y la ficha del jugador con tope por pasada')
    wf = open('.github/workflows/precalculo_dia.yml', encoding='utf-8').read()
    check('python acumular_itf.py' in wf and 'historico_itf_vivo.csv' in wf,
          'v480 tenis: el ITF de BetExplorer se acumula y se publica en CADA precálculo')
    rt = open('.github/workflows/retrain_leagues.yml', encoding='utf-8').read()
    check('timeout-minutes: 150' in rt, 'v480: el reentrenamiento con 150 min (se cortaba a los 90 y no publicaba nada)')


def probar_copas():
    import exportar_web as ew
    import errores_web
    viejo = errores_web.casa_del_partido
    tabs = {('SSV Jeddeloh II', 'Hertha'): {'1x2': {'home': 0.03, 'draw': 0.04, 'away': 0.93}}}
    errores_web.casa_del_partido = lambda h, a, *x, **k: tabs.get((h, a), {})
    filas = [{'deporte': 'Fútbol', 'liga': 'DFB-Pokal', 'partido': 'SSV Jeddeloh II vs Hertha', 'apuesta': 'Gana SSV Jeddeloh II', 'prob': 0.506},
             {'deporte': 'Fútbol', 'liga': 'Copa del Rey', 'partido': 'CD Minera vs Cartagena', 'apuesta': 'Gana CD Minera', 'prob': 0.594},
             {'deporte': 'Fútbol', 'liga': 'LaLiga', 'partido': 'Girona vs Celta', 'apuesta': 'Gana Girona', 'prob': 0.6}]
    try:
        n = ew.sugerencia_de_la_casa(filas, {'ger_dfb_pokal': 'DFB-Pokal', 'esp_copa_rey': 'Copa del Rey'})
    finally:
        errores_web.casa_del_partido = viejo
    check(n == 1 and filas[0]['apuesta'] == 'Gana Hertha' and filas[0]['prob'] == 0.93 and filas[0]['fuente'] == 'casa',
          'v480 copas: la sugerencia es la de la casa («la casa ve Gana Hertha 93 %», no el amateur al 51 %)')
    check(filas[1]['apuesta'] == '' and filas[1]['prob'] is None, 'v480 copas: sin precio de la casa, sin sugerencia (nunca el disparate del modelo)')
    check(filas[2]['apuesta'] == 'Gana Girona', 'v480 copas: las ligas no se tocan')
    app = open(os.path.join('web', 'app.js'), encoding='utf-8').read()
    check("p.fuente === 'casa' ? 'la casa ve' : 'el modelo ve'" in app, 'v480 copas: la página dice «la casa ve»')


if __name__ == '__main__':
    probar_kbo()
    probar_tenis()
    probar_copas()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
