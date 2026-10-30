#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v528 — combinadas de 3 patas con la regla medida (💎/🔷, acierto real por banda de cuota, 1,30-2,60; 35 → 63 %
simulado, p5 +9,6) y la combinada que sugiere la IA (una al día, dentro de la misma regla, medida aparte). Sin red."""
import datetime as dt
import io
import json
import os

import combinadas_web as cw

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
    check(cw.TIPOS['alta'] == {'patas': 3, 'cuota': (1.30, 2.60), 'solo_altos': True, 'por_acierto': 'banda'},
          'v528: 3 patas = 💎/🔷 por acierto real por banda de cuota, cuota total 1,30-2,60')
    check(cw.TIPOS['combinada']['cuota'] == (1.20, 1.60) and cw.TIPOS['combinada']['por_acierto'] is True,
          'v528: las de 2 patas no cambian (la banda subía 72 → 76 % pero p5 −5,3)')
    check(cw.banda({'cuota': 1.12}) == 2 and cw.banda({'cuota': 1.6}) == 8, 'v528: bandas de cuota de 0,05')
    cb = cw.calibracion_banda([{'cuota': 1.12, 'estado': 'verde'}] * 10 + [{'cuota': 1.32, 'estado': 'roja'}] * 10)
    check(cb[2] > 0.85 and cb[6] < 0.5, 'v528: la calibración por banda sale del acierto real')
    ahora = dt.datetime(2026, 10, 30, 12, 0, tzinfo=dt.timezone.utc)
    ini = (ahora + dt.timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')
    ps = [{'id': 'p%d' % i, 'partido': 'A%d vs B%d' % (i, i), 'deporte': 'Fútbol', 'apuesta': 'X', 'cuota': c, 'prob': pr, 'elige': el,
           'estado': 'pendiente', 'inicio': ini} for i, (c, pr, el) in enumerate([(1.12, 0.88, True), (1.15, 0.87, True), (1.18, 0.86, False),
                                                                                  (1.35, 0.80, False), (1.40, 0.79, False), (1.14, 0.9, True)])]
    cbh = {2: 0.92, 3: 0.88, 4: 0.80, 7: 0.70}
    out = [c for c in cw.armar(ps, {}, ahora, {}, cbh) if c['tipo'] == 'alta' and c['alcance'] == 'Fútbol']
    check(out and all(float(p['prob']) >= 0.85 or p['id'] in ('p0', 'p1', 'p5') for p in out[0]['patas']) and 1.30 <= out[0]['cuota'] <= 2.60,
          'v528: la de 3 patas sólo con 💎/🔷 y dentro de su cuota')
    # la de la IA: con Gemini de mentira
    import requests

    class R:
        def __init__(self, ids):
            self.ok = True
            self._t = json.dumps({'ids': ids, 'motivo': 'x'})

        def json(self):
            return {'candidates': [{'content': {'parts': [{'text': self._t}]}}]}
    orig = requests.post
    os.environ['GEMINI_API_KEY'] = 'prueba'
    try:
        requests.post = lambda *a, **k: R(['p0', 'p1', 'p5'])
        r = cw.combinada_ia(ps, {}, ahora, cbh, set())
        check(len(r) == 1 and r[0]['alcance'] == 'IA' and r[0]['tipo'] == 'alta' and len(r[0]['patas']) == 3, 'v528: la IA arma su combinada de 3 patas')
        check(cw.combinada_ia(ps, {}, ahora, cbh, {'2026-10-30'}) == [], 'v528: una al día (si ya hay, no se vuelve a preguntar)')
        requests.post = lambda *a, **k: R(['p0', 'p1'])
        check(cw.combinada_ia(ps, {}, ahora, cbh, set()) == [], 'v528: si la IA propone algo fuera de la regla, ese día no hay')
    finally:
        requests.post = orig
        os.environ.pop('GEMINI_API_KEY', None)
    sim = json.loads(leer('web', 'combinadas_simuladas.json'))
    t = sim.get('tres') or {}
    check(t.get('hasta') == '2026-10-29' and len(t.get('combinadas') or []) >= 40 and all(c['tipo'] == 'alta' for c in t['combinadas']),
          'v528: las de 3 patas del 15 al 29-oct rehechas con la regla nueva')
    app = leer('web', 'app.js')
    check("const DESDE_TRES = '2026-10-30';" in app and "fila('✨ IA + modelo (3 patas)'" in app and 'Cuota alta (3 patas)' not in app,
          'v528: la página cuenta las rehechas hasta el 29, las publicadas desde el 30 y la de la IA aparte')
    check('GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}' in leer('.github', 'workflows', 'sitio_web.yml'), 'v528: el sitio tiene la clave para la combinada de la IA')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
