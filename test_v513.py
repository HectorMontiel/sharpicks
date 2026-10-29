#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v513 — Pulso SharPicks: el modelo medido carga, da lo medido (0-0 al 75' ≈ 46 % de otro gol), la cuenta de
Python (historial) es la misma que la de la página, el gratis y el VIP/monedas, y el historial público. Sin red."""
import io
import json
import os

import pulso_historial as ph

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*r):
    with io.open(os.path.join(AQUI, *r), encoding='utf-8') as fh:
        return fh.read()


def probar():
    M = json.loads(leer('web', 'pulso_modelo.json'))
    check(set(M['modelos']) == {'gol', 'gol2', 'gol_l', 'gol_v', 'cor1', 'cor2', 'cor3', 'gol_sf', 'gol2_sf', 'gol_l_sf'},
          'v513: los 7 mercados medidos (v518: y los 3 de goles sin fuerza previa)')
    for k, m in M['modelos'].items():
        check(len(m['coef']) == len(m['cols']) and m['tabla'] and m['n'] > 15000, 'v513: %s con coeficientes y su tabla (%d estados)' % (k, m['n']))
    ctx = {'sl': {'n': 10, 'gf': 1.6, 'gc': 1.1}, 'sv': {'n': 10, 'gf': 1.2, 'gc': 1.4}}
    p75 = ph.prob(M, 'gol', ph.rasgos(M, ctx, 75.0, 0, 0, 7))
    p60 = ph.prob(M, 'gol', ph.rasgos(M, ctx, 60.0, 0, 0, 5))
    check(0.38 <= p75 <= 0.54 and 0.56 <= p60 <= 0.72 and p60 > p75, 'v513: 0-0 al 60 (%.2f) y al 75 (%.2f) como lo medido (65 %% y 46 %%)' % (p60, p75))
    c = ph.prob(M, 'cor2', ph.rasgos(M, ctx, 60.0, 0, 0, 5))
    check(0.7 <= c <= 0.95, 'v513: 2 córners más desde el 60 con 5 hasta ahora (%.2f)' % c)
    check(ph.prob(M, 'gol', ph.rasgos(M, ctx, 55.0, 0, 0, 3)) <= ph.TOPE['gol'], 'v513: el tope de lo que lo medido no sostiene')
    sf = ph.rasgos(M, {}, 60.0, 0, 0, 5)
    check(0.5 <= ph.prob(M, 'gol', sf) <= ph.TOPE_SF['gol'] and ph.prob(M, 'gol_v', sf) is None and ph.prob(M, 'cor2', sf) is not None,
          'v518: sin pick (sin fuerza previa) hay Pulso de goles con su tope y córners; el visitante no (no pasó)')
    check("const TOPE_SF = { gol: 0.8, gol2: 0.45, gol_l: 0.7 };" in leer('web', 'pulso.js') and ph.TOPE_SF == {'gol': 0.8, 'gol2': 0.45, 'gol_l': 0.7},
          'v518: los mismos topes sin fuerza en la página y en el historial')
    check(ph.prob(M, 'gol', ph.rasgos(M, ctx, 50.0, 0, 0, 3)) is None and ph.prob(M, 'cor2', ph.rasgos(M, ctx, 50.0, 0, 0, 3)) is not None,
          "v517: goles desde el 55' y córners desde el 46' (lo medido)")
    js = leer('web', 'pulso.js')
    check("const TOPE = { gol: 0.85, gol2: 0.5, gol_l: 0.75, gol_v: 0.65 }" in js and ph.TOPE == {'gol': 0.85, 'gol2': 0.5, 'gol_l': 0.75, 'gol_v': 0.65},
          'v513: los mismos topes en la página y en el historial')
    check('(enc(sl.gf, sl.n) + enc(sv.gc, sv.n)) / 2 * rem / 94' in js and "enc(sl.get('gf'), sl.get('n')) + enc(sv.get('gc'), sv.get('n'))" in leer('pulso_historial.py'),
          'v513: la misma cuenta de la fuerza en la página y en el historial')
    check("const GRATIS = { gol: 1, cor2: 1 };" in js and 't && t.n >= 100 ? t : null' in js, 'v513: gratis «otro gol» y «2 córners»; «salió» sólo con 100+ casos')
    check(ph.prob(M, 'gol', ph.rasgos(M, ctx, 85.0, 0, 0, 8)) is None and ph.prob(M, 'cor2', ph.rasgos(M, ctx, 85.0, 0, 0, 8)) is not None,
          'v513: goles sólo hasta el 80\' y córners hasta el 85\' (lo medido; más allá el modelo inventa)')
    check('const HASTA = { gol: 80, gol2: 80, gol_l: 80, gol_v: 80, cor1: 85, cor2: 85, cor3: 85 };' in js and '1 - prob' not in js,
          'v513: la página respeta lo medido y sin dato no inventa un 100 %')
    app = leer('web', 'app.js')
    check('function pulsoHtml(p, v, vs, L, V, abierto)' in app and 'data-pulso-abrir' in app and 'PULSO.delPick(real, p, v, vs)' in app,
          'v513: el Pulso en «Ver partido», con monedas y tus picks en vivo')
    check('pulsoChip(p, v)' in app, 'v513: el chip del Pulso en la tarjeta en vivo')
    check("/FIRST_HALF/.test(v.est || '')" in js and 'const DESDE = { gol: 55' in js and 'function mejor(ms, abierto)' in js,
          'v517: el Pulso sólo en el 2.º tiempo y con su «Mejor ahora»')
    check("/^STATUS_HALFTIME$/.test(v.est || '')" in js and "/HALF|Medio/i.test(v.est" not in js,
          'v517: «STATUS_SECOND_HALF» no se confunde con el descanso (daba 45,5 a todo el 2.º tiempo)')
    check('Medido en 3.424' not in app and 'pulso-grid' in app and "h = h.replace('<!--PULSO-->', pulsoArriba);" in app,
          'v517: compacto, sin el texto de abajo y debajo de la cancha')
    check("seccion('stats', ico('chart-column') + ' Estadísticas'" in app and "seccionStats(compensacion(p, v) + miniStats(v, p))" in app,
          'v517: Ver partido y la tarjeta seccionados (la cancha a la vista)')
    check("candidatosPulso(grupos)" in app and "ico('target') + ' Candidatos Pulso" in app, 'v517: Candidatos Pulso arriba de En vivo')
    check('📈' not in app.split('const EMOJI_ICO')[1].split('};')[1] and 'id="i-activity"' in leer('web', 'iconos.svg'),
          'v517: el Pulso con su ícono del sprite, sin emojis')
    check("document.addEventListener('visibilitychange'" in app and 'vivo(); vivo365(); vivoFs();' in app and 'estado.vivoDesde' in app,
          'v518: al volver a la app el marcador y el minuto se piden al instante')
    check('function statsHueco(v, p)' in app and "!statsHueco(v, p)" in app and 'const quien = ' in app,
          'v518: ESPN con sólo faltas y tarjetas cuenta como sin estadísticas (respaldo); el gol dice sólo quién')
    cu = leer('web', 'cuenta.js')
    check("sb.rpc('desbloquear_pulso'" in cu and "from('pulso_desbloqueos')" in cu and "from('pulso_historial')" in cu,
          'v513: abrir con monedas y el historial público')
    html = leer('web', 'index.html')
    check(html.index('<script src="pulso.js">') < html.index('<script src="app.js">') and 'id="pulso-hist"' in html, 'v513: pulso.js antes de app.js y su sección en Historial')
    sq = leer('supabase', 'v513_pulso.sql')
    check('create or replace function public.desbloquear_pulso' in sq and 'public.es_pro()' in sq and "'precio_pulso'" in sq,
          'v513: el cobro con monedas va en el servidor (el VIP no paga)')
    check('resolution=ignore-duplicates' in leer('pulso_historial.py'), 'v513: lo apuntado no se retoca')
    check('python pulso_historial.py' in leer('.github', 'workflows', 'sitio_web.yml'), 'v513: el historial se apunta en cada pasada del sitio')
    # una lectura completa con un partido de ejemplo
    e = {'goles': [(55.0, 1, 0), (80.0, 1, 1)], 'cor': [5, 20, 33, 47, 58, 62, 66, 71, 88], 'fin': (1, 1)}
    L = ph.lecturas(M, {'partido': 'A vs B', 'fecha': '2026-10-29', 'ctx': ctx}, e)
    d = {(x['minuto'], x['mercado']): x for x in L}
    check(d[(60, 'gol')]['marcador'] == '1-0' and d[(60, 'gol')]['acierto'] is True and d[(70, 'gol_l')]['acierto'] is False,
          'v513: el historial liquida con el marcador final')
    check(d[(70, 'cor2')]['acierto'] is True and d[(70, 'cor3')]['acierto'] is False and d[(60, 'cor3')]['acierto'] is True,
          'v513: los córners también (7 al 70, 9 al final)')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
