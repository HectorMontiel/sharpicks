#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v483 — el día (Hoy / Mañana / «jue 30 oct») en las tarjetas de Destacados y «Para ti», con los de hoy
primero; y los planes cortos (precio, un número grande, lo clave, el botón) que se abren al tocarlos. Sin red."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*p):
    return open(os.path.join(AQUI, *p), encoding='utf-8').read()


def probar():
    app, html, cta, css = leer('web', 'app.js'), leer('web', 'index.html'), leer('web', 'cuenta.js'), leer('web', 'estilo.css')
    # 1) la fecha en las tarjetas
    check('function diaCorto(p)' in app and "'Hoy'" in app and "'Mañana'" in app and "weekday: 'short'" in app,
          'v483: las tarjetas dicen Hoy, Mañana o el día con la fecha')
    d = app[app.index('function destacado('):]
    check("relojDia(ps) + '</div>'" in d[:1800], 'v483: Destacados y «Para ti» usan el reloj con el día')
    check('(dias.indexOf(diaDe(a.p)) - dias.indexOf(diaDe(b.p))) || (b.s - a.s)' in app,
          'v483: en «Para ti» van primero los de hoy y luego por puntos')
    check('.dest-cuando.hoy small' in css, 'v483: «Hoy» resalta')
    # 2) planes cortos que se despliegan
    planes = html[html.index('<div class="planes-grid">'):html.index('<p class="aviso">🎉')]
    check(planes.count('data-plan-abre') == 3 and planes.count('<details class="plan-mas">') == 3,
          'v483: los tres planes se abren al tocarlos')
    vip = planes[planes.index('id="plan-vip"'):]
    corto = vip[:vip.index('<details')]
    check('Hacerme VIP' in corto and 'id="gancho-vip"' in corto and corto.count('<li>') <= 3,
          'v483: lo que se ve del VIP es corto: precio, número grande, 3 puntos y el botón')
    check('Arma tu parley con la IA' in vip and 'Combinadas de 2 a 20 patas' in vip and 'id="numeros-vip"' in vip[vip.index('<details'):],
          'v483: el detalle completo (y los números reales) sigue, dentro del desplegable')
    check("gancho('gancho-vip', ['Diamante', 'Platino', 'Plata'])" in cta and 'x.verdes + x.rojas >= 30' in cta
          and 'x.verdes / (x.verdes + x.rojas) >= 0.75' in cta,
          'v483: el número grande es el mejor acierto real con 30+ partidos y 75 %+')
    check("e.target.closest('[data-plan-abre]')" in cta and "e.target.closest('button, a, summary" in cta,
          'v483: tocar el plan lo abre, pero sus botones siguen funcionando')


def probar_buscador():
    """El buscador: todos los días y deportes, sin acentos, con pausa al escribir, y sin repintar caro."""
    app = leer('web', 'app.js')
    check("const buscando = !!q && ['picks', 'vivo'].includes(estado.vista)" in app
          and 'let lista = buscando ? paraBuscar(q) : listaConAnalisis()' in app,
          'v483 buscador: con texto busca en todos los días cargados (no sólo en la pestaña)')
    check('if (estado.deportes.size && !buscando)' in app and "estado.niveles.size && !buscando" in app
          and 'estado.liga && !buscando' in app, 'v483 buscador: sin el filtro de deporte, nivel ni liga')
    check(".normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')" in app, 'v483 buscador: sin acentos («América» = «Club America»)')
    check('(estado.analisis || []).filter((a) => textoBusca(a).includes(q)' in app,
          'v483 buscador: también encuentra los partidos sin pick (tarjetas de análisis)')
    check('if (buscando) { pintarBusqueda(grupos); return; }' in app and 'agrupar(buscando ? lista : listaConAnalisis())' in app,
          'v483 buscador: resultados por día y se pueden abrir')
    check('_tBusca = setTimeout(' in app and ', 250);' in app, 'v483 buscador: espera a que dejes de escribir (250 ms)')
    # la traba: no crear formateadores de fecha en cada llamada
    check(app.count('new Intl.DateTimeFormat') == 1 and 'const FMT = (o) => new Intl.DateTimeFormat' in app,
          'v483: los formateadores de fecha se crean una sola vez (antes, miles por repintado)')
    check('_MEMO_DIADE = new WeakMap()' in app and '_MEMO_DIA.get(t)' in app, 'v483: el día de cada pick se recuerda, sin tocar el pick')


def probar_penales():
    """La Leagues Cup va directo a penales (sin prórroga): su empate a 90' se queda en el entreno; en una
    copa con prórroga (Copa del Rey) el partido a penales sigue fuera."""
    import sys
    sys.path.insert(0, AQUI)
    import espn_fechas
    import uefa_scraper as us

    def ev(st, gh, ga, dia):
        eq = lambda lado, n, g: {'homeAway': lado, 'team': {'displayName': n}, 'score': str(g)}
        return {'date': '2026-08-%02dT02:00Z' % dia, 'competitions': [{'status': {'type': {'name': st, 'completed': True}},
                'competitors': [eq('home', 'Columbus Crew', gh), eq('away', 'Pumas UNAM', ga)], 'venue': {}}]}
    viejo = espn_fechas.eventos
    espn_fechas.eventos = lambda *a, **k: [ev('STATUS_FINAL_PEN', 1, 1, 11), ev('STATUS_FULL_TIME', 2, 1, 12), ev('STATUS_FINAL_AET', 3, 2, 13)]
    try:
        lc = us.descargar_espn('concacaf.leagues.cup', '2026-08-01', '2026-08-31', pausa=0)
        cr = us.descargar_espn('esp.copa_del_rey', '2026-08-01', '2026-08-31', pausa=0)
    finally:
        espn_fechas.eventos = viejo
    check(len(lc) == 2 and ((lc.home_goals == 1) & (lc.away_goals == 1)).sum() == 1,
          'v483: la Leagues Cup conserva su empate que se fue a penales (y la prórroga sigue fuera)')
    check(len(cr) == 1, 'v483: en la Copa del Rey los partidos a penales o con prórroga siguen fuera del entreno')
    import pandas as pd
    h = pd.read_csv(os.path.join(AQUI, 'historico_leagues_cup.csv'))
    h = h[h.competicion == 'leagues_cup']
    check(len(h) >= 260 and (h.home_goals == h.away_goals).sum() >= 60,
          'v483: el histórico de la Leagues Cup tiene otra vez sus empates (%d partidos, %d empates)'
          % (len(h), (h.home_goals == h.away_goals).sum()))


if __name__ == '__main__':
    probar()
    probar_buscador()
    probar_penales()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
