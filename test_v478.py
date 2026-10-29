#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v478 — bugs del handoff del 27-oct. Bug 2: al empezar el partido Playdoit lo saca de su catálogo
pre-partido y la pasada siguiente dejaba el partido en vivo sin las líneas de la casa ni el parley;
ahora se conserva el `lin` con casa de lo publicado antes. Sin red."""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar_bug2():
    import exportar_web as ew
    ahora = dt.datetime(2026, 10, 27, 20, 0, tzinfo=dt.timezone.utc)
    con_casa = {'goles': {'h': [1]}, 'casa': True, 'par': [['goles', 'h', '0.5', 0.8]]}
    previas = {('2026-10-27', 'A vs B'): con_casa, ('2026-10-27', 'C vs D'): con_casa, ('2026-10-27', 'E vs F'): con_casa}
    compartido = {'fl': 'GGG', 'lin': {'casa': False}}
    filas = [
        {'deporte': 'Fútbol', 'partido': 'A vs B', 'fecha': '2026-10-27', 'inicio': '2026-10-27 19:00:00', 'ctx': compartido},
        {'deporte': 'Fútbol', 'partido': 'A vs B', 'fecha': '2026-10-27', 'inicio': '2026-10-27 19:00:00', 'ctx': compartido},
        {'deporte': 'Fútbol', 'partido': 'C vs D', 'fecha': '2026-10-27', 'inicio': '2026-10-27 21:00:00', 'ctx': {'fl': 'P'}},
        {'deporte': 'Fútbol', 'partido': 'E vs F', 'fecha': '2026-10-27', 'inicio': '2026-10-27 18:00:00',
         'ctx': {'lin': {'casa': True, 'nueva': 1}}},
        {'deporte': 'Fútbol', 'partido': 'G vs H', 'fecha': '2026-10-27', 'inicio': '2026-10-27 18:00:00'},
        {'deporte': 'Tenis', 'partido': 'A vs B', 'fecha': '2026-10-27', 'inicio': '2026-10-27 18:00:00'},
    ]
    n = ew.conservar_lin_casa(filas, previas, ahora)
    check(n == 2 and filas[0]['ctx']['lin'] is con_casa and filas[1]['ctx']['lin'] is con_casa,
          'v478 bug 2: el partido que ya empezó recupera las líneas con casa de la pasada anterior')
    check(filas[0]['ctx']['fl'] == 'GGG' and compartido['lin'] == {'casa': False},
          'v478 bug 2: se conserva el resto del contexto y no se toca el ctx compartido')
    check('lin' not in filas[2]['ctx'], 'v478 bug 2: el que todavía no empieza se queda con lo que calcule esta pasada')
    check(filas[3]['ctx']['lin'].get('nueva') == 1, 'v478 bug 2: si esta pasada sí trae la casa, manda la nueva')
    check('ctx' not in filas[4] and 'ctx' not in filas[5], 'v478 bug 2: sin línea previa (o sin fútbol) no se inventa nada')
    check(not ew._ya_empezo({'inicio': None}, ahora) and not ew._ya_empezo({'inicio': 'mañana'}, ahora),
          'v478 bug 2: sin hora de inicio válida no cuenta como empezado')
    src = open('exportar_web.py', encoding='utf-8').read()
    check('conservar_lin_casa(picks + analisis, _lin_publicadas())' in src, 'v478 bug 2: el exportador lo aplica en cada pasada')


def probar_tiros_mitades():
    import numpy as np
    import tiros_seguimiento as ts
    # el caso real del 27-oct: bien en total y en la 2.ª mitad, mal en la 1.ª → no pasa
    fechas = ['2026-09-%02d' % (10 + i // 10) for i in range(100)] + ['2026-10-%02d' % (1 + i // 30) for i in range(300)]
    gan = [(-1.0 if i % 2 else 0.6) for i in range(100)] + [(0.8 if i % 3 else -1.0) for i in range(300)]
    partidos = ['p%d' % i for i in range(400)]
    m = ts._p5_mitades(fechas, partidos, gan, 1)
    check(m[0] < 0 < m[1] and ts._p5(partidos, gan, 1) > 0,
          'v478 tiros: con la 1.ª mitad en rojo no basta el p5 global (%s)' % [round(x, 3) for x in m])
    src = open('tiros_seguimiento.py', encoding='utf-8').read()
    check(src.count('and all(x > 0 for x in mit)') == 2, 'v478 tiros: las dos reglas (base y alta) exigen p5 > 0 en las DOS mitades')
    check(np.isnan(ts._p5_mitades([], [], [], 1)[0]), 'v478 tiros: sin datos, sin mitades')


def probar_bug3_categoria():
    import escudos
    check(escudos._cat('Liga FUTVE', 'Carabobo', 'Deportivo La Guaira') == (False, False)
          and escudos._cat('Liga Fútbol Nacional') == (False, False),
          'v478 bug 3: «Liga FUTVE» ya no es femenil (casaba «liga f» por dentro y perdía la casa)')
    check(all(escudos._cat(x)[0] for x in ('Liga F', 'Bundesliga Fem', 'NWSL', 'WSL', 'Liga MX Femenil', 'Cruz Azul (F)',
                                           'Mujeres Super League', 'FA Women - Division One')),
          'v478 bug 3: las femeniles se siguen reconociendo (también «Mujeres Super League» de Playdoit)')


def probar_bug1_noticias():
    import types
    import ia_gemini as ia
    rss = ('<rss><channel>'
           '<item><title>América pierde a Jesús Medina por lesión - Récord</title><pubDate>Fri, 23 Oct 2026 10:00:00 GMT</pubDate></item>'
           '<item><title>América Femenil llega sin Scarlett Camberos - ESPN</title><pubDate>Fri, 23 Oct 2026 11:00:00 GMT</pubDate></item>'
           '</channel></rss>')
    pedidos = []
    falso = types.SimpleNamespace(get=lambda url, params=None, timeout=None, headers=None: (
        pedidos.append(params['q']) or types.SimpleNamespace(ok=True, text=rss)))
    viejo_r, viejo_s = sys.modules.get('requests'), ia.time.sleep
    sys.modules['requests'], ia.time.sleep = falso, (lambda s: None)
    try:
        fem = ia.noticias_rss([{'partido': 'Atlético de San Luis vs América', 'liga': 'Liga MX Femenil', 'inicio': '2026-10-24 19:00:00'}])
        var = ia.noticias_rss([{'partido': 'Atlético de San Luis vs América', 'liga': 'Liga MX', 'inicio': '2026-10-24 19:00:00'}])
    finally:
        if viejo_r is not None:
            sys.modules['requests'] = viejo_r
        else:
            sys.modules.pop('requests', None)
        ia.time.sleep = viejo_s
    nf = (fem.get('Atlético de San Luis vs America') or fem.get('Atlético de San Luis vs América') or {}).get('noticias')
    nv = (var.get('Atlético de San Luis vs América') or {}).get('noticias')
    check(nf == ['América Femenil llega sin Scarlett Camberos'], 'v478 bug 1: en el femenil sólo las noticias del femenil: %s' % nf)
    check(nv == ['América pierde a Jesús Medina por lesión'], 'v478 bug 1: en el varonil, fuera las del femenil: %s' % nv)
    check(len(pedidos) == 2 and 'femenil' in pedidos[0] and 'femenil' not in pedidos[1],
          'v478 bug 1: la búsqueda lleva «femenil» sólo cuando la liga lo es: %s' % pedidos)


def probar_bug7_pendientes():
    import liquidar_pendientes as lp
    check(lp.ABIERTOS == 'in.(pendiente,vivo)' and lp.DIAS >= 15, 'v478 bug 7: se revisan también los «vivo» (395 de 462 se quedaban así)')
    src = open('liquidar_pendientes.py', encoding='utf-8').read()
    check("'estado': ABIERTOS" in src and src.count('ABIERTOS') >= 3 and "'offset': 1000 * pag" in src,
          'v478 bug 7: la consulta y el cierre aceptan «vivo», y van por páginas de 1000')
    check(lp._tenista('Yushan Shao', 'Shao Y.') and lp._tenista('Juan Manuel Cerundolo', 'Cerundolo J. M.')
          and lp._tenista('Lejla Hana Golubovic', 'Golubovic L. H.'),
          'v478 bug 7: «Apellido I.» de Flashscore empareja con el nombre completo')
    check(not lp._tenista('Yushan Shao', 'Shao X.') and not lp._tenista('Yushan Shao', 'Lin Y. J./Shao Y.')
          and not lp._tenista('Anna Yang', 'Yang Z.'),
          'v478 bug 7: otra inicial o un partido de dobles no cuentan')
    viejo = lp._feed_fs
    feeds = {-2: [{'home': 'Taddia L.', 'away': 'Mugelli P.', 'gh': 0, 'ga': 2}], -1: [{'home': 'Taddia L.', 'away': 'Fellows J.', 'gh': 2, 'ga': 0}]}
    lp._feed_fs = lambda dep, o, sesion: feeds.get(o, [])
    try:
        hoy = dt.datetime.now(dt.timezone.utc)
        r = lp._flashscore('Tenis', hoy - dt.timedelta(days=4), 'Pietro Mugelli', 'Leonardo Taddia', None)
    finally:
        lp._feed_fs = viejo
    check(r and r['g'] == (2, 0), 'v478 bug 7: el ITF se busca en los 8 días del feed y con los lados enderezados: %s' % r)


def probar_bug8_css():
    css = open(os.path.join('web', 'estilo.css'), encoding='utf-8').read()
    check('@supports not (overflow: clip)' in css and '.liga-bloque { overflow: visible; }' in css,
          'v478 bug 8: en iOS sin «overflow: clip» el bloque no recorta y «Cerrar» se pega')


if __name__ == '__main__':
    probar_bug2()
    probar_tiros_mitades()
    probar_bug3_categoria()
    probar_bug1_noticias()
    probar_bug7_pendientes()
    probar_bug8_css()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
