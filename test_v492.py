#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v492 — los últimos 5 partidos de verdad (no el promedio) y la tabla de clasificación de la liga con los
dos equipos resaltados. v493 — el minuto real desde que carga (lista del día de 365Scores) para lo que sólo
da Flashscore («1.ª parte»). Sin red."""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*p):
    with open(os.path.join(AQUI, *p), encoding='utf-8') as fh:
        return fh.read()


def probar_ultimos():
    import pandas as pd
    import errores_web as ew
    h = pd.DataFrame({
        'date': pd.to_datetime(['2026-10-01', '2026-10-05', '2026-10-09', '2026-10-13', '2026-10-17', '2026-10-21', '2026-10-30']),
        'home_team': ['A', 'B', 'A', 'C', 'A', 'D', 'A'], 'away_team': ['X', 'A', 'Y', 'A', 'Z', 'A', 'W'],
        'home_goals': [1, 2, 0, 1, 3, 0, 9], 'away_goals': [0, 2, 1, 4, 1, 0, 9],
        'home_corners': [5, 4, 3, 2, 6, 1, 9], 'away_corners': [2, 6, 7, 5, 3, 8, 9],
        'home_shots_on': [4, 3, 2, 1, 5, 2, 9], 'away_shots_on': [1, 5, 4, 6, 2, 3, 9],
        'home_yellow': [1, 2, 0, 3, 1, 2, 9], 'away_yellow': [2, 1, 1, 0, 2, 1, 9],
        'stats_origen': [None] * 7})
    u = ew._ultimos(h, 'A', pd.Timestamp('2026-10-28'), 'prueba')
    check(len(u) == 5 and u[0][1] == 'D' and u[0][2] == 0 and u[-1][1] == 'B',
          'v492: los 5 más recientes antes del partido, del más nuevo al más viejo (y nada posterior)')
    check(u[0][3:5] == [0, 0] and u[1][3:5] == [3, 1] and u[2][3:5] == [4, 1],
          'v492: el marcador desde el lado del equipo (a favor-en contra), de local y de visita')
    check(u[2][5] == [5, 2] and u[2][6] == [6, 1] and u[2][7] == [0, 3],
          'v492: córners, a puerta y amarillas del equipo contra las del rival (de visita, volteadas)')
    # filas del generador (no observadas) → None, nunca un número falso
    ew._MEMO_REALES.clear()
    import rendimiento_equipos as re_
    viejo = re_._solo_reales
    re_._solo_reales = lambda d, c: d.iloc[0:0]
    try:
        u2 = ew._ultimos(h, 'A', pd.Timestamp('2026-10-28'), 'prueba2')
    finally:
        re_._solo_reales = viejo
    check(all(x[5] is None and x[6] is None and x[7] is None for x in u2) and u2[0][3:5] == [0, 0],
          'v492: sin estadística real del partido sale «—» (None); los goles siempre')
    src = leer('errores_web.py')
    check("ul, uv = _ultimos(h, home, antes, clave), _ultimos(h, away, antes, clave)" in src, 'v492: el contexto lleva ul/uv')


def probar_tablas():
    import tablas_web as tw
    resp = {'children': [{'name': 'Eastern Conference', 'standings': {'entries': [
        {'team': {'displayName': 'Nashville SC'}, 'note': {'description': 'Qualifies for Playoffs'},
         'stats': [{'name': 'rank', 'value': 1}, {'name': 'gamesPlayed', 'value': 31}, {'name': 'wins', 'value': 21},
                   {'name': 'ties', 'value': 7}, {'name': 'losses', 'value': 3}, {'name': 'pointDifferential', 'value': 43},
                   {'name': 'points', 'value': 70}]},
        {'team': {'displayName': 'Philadelphia Union'},
         'stats': [{'name': 'rank', 'value': 6}, {'name': 'gamesPlayed', 'value': 31}, {'name': 'points', 'value': 46},
                   {'name': 'pointDifferential', 'displayValue': '+9'}]}]}}]}
    g = tw.leer(resp)
    check(len(g) == 1 and g[0]['nombre'] == 'Eastern Conference' and g[0]['filas'][0][:2] == [1, 'Nashville SC']
          and g[0]['filas'][0][7] == 70 and g[0]['filas'][1][6] == 9, 'v492: la tabla de ESPN se lee (grupo, posición, puntos, DG)')
    pedidos = []
    t = tw.generar([{'deporte': 'Fútbol', 'liga': 'MLS', 'partido': 'A vs B'}, {'deporte': 'Fútbol', 'liga': 'MLS', 'partido': 'C vs D'},
                    {'deporte': 'Tenis', 'liga': 'ATP', 'partido': 'E vs F'}],
                   {'A vs B': 'mls', 'C vs D': 'mls'}, pedir=lambda u: pedidos.append(u) or resp)
    check(list(t) == ['MLS'] and len(pedidos) == 1 and 'usa.1' in pedidos[0], 'v492: una consulta por liga, sólo fútbol con código de ESPN')
    ew = leer('exportar_web.py')
    check("tablas_web.escribir(tablas_web.generar(picks + analisis, claves_t)" in ew, 'v492: el exportador escribe tablas.json')
    import tempfile
    d = tempfile.mkdtemp()
    ruta = os.path.join(d, 'no', 'existe', 'tablas.json')
    check(tw.escribir({'MLS': {'grupos': g}}, ruta) == 1 and os.path.exists(ruta), 'v492: escribe aunque la carpeta no exista todavía')


def probar_web():
    app, css = leer('web', 'app.js'), leer('web', 'estilo.css')
    check('function formaEquipo(nombre, f, u)' in app and "formaEquipo(L, ctx.fl, ctx.ul) + formaEquipo(V, ctx.fv, ctx.uv)" in app,
          'v492: cada equipo de «Forma» despliega sus 5 partidos')
    check("const par = (x) => (Array.isArray(x) ? x[0] + '-' + x[1] : '—');" in app, 'v492: sin dato real, «—»')
    check("if (tb) h += sub('Clasificación', tb);" in app and "f === yoL || f === yoV ? ' yo' : ''" in app
          and "fetch('datos/tablas.json?x='" in app, 'v492: pestaña «Clasificación» con la tabla entera y los dos resaltados')
    check("contextoHtml((ps.find((x) => x.ctx) || {}).ctx, L, V, p.liga)" in app, 'v492: la tarjeta pasa la liga')
    check('.u5-f { display: grid;' in css and '.tl-f.yo {' in css, 'v492: estilos compactos')
    check("gt: g.statusGroup === 3 && Number(g.gameTime) > 0 ? Number(g.gameTime) : null" in app
          and 'async function minutos365()' in app and 'setInterval(minutos365, 60 * 1000);' in app,
          'v493: el minuto de la lista del día de 365Scores para lo que llega sin minuto')
    check("const t = m3.gt + Math.floor((Date.now() - m3.ts) / 60e3)" in app, 'v493: entre consulta y consulta el minuto corre solo')


if __name__ == '__main__':
    probar_ultimos()
    probar_tablas()
    probar_web()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
