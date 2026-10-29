#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v520 — el Pulso en vivo del servidor (pulso_vivo.py): la misma cuenta que la página, la clave del partido igual
que la de los desbloqueos, aviso sólo a lo de 75 %+ y una sola vez, la IA sólo elige entre los mercados medidos,
y lo recomendado se liquida con el marcador y los córners finales. Sin red (ESPN, Supabase y Telegram de mentira)."""
import io
import json
import os

import pulso_historial as ph
import pulso_vivo as pv

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*r):
    with io.open(os.path.join(AQUI, *r), encoding='utf-8') as fh:
        return fh.read()


def resumen(estado='in', periodo=2, reloj="72'", gh=1, ga=1, cor=(4, 3), fin=False):
    eq = lambda i, s, c: {'homeAway': 'home' if i == 1 else 'away', 'score': str(s), 'team': {'id': str(i)}}
    return {'header': {'competitions': [{'status': {'period': periodo, 'displayClock': reloj,
                                                    'type': {'state': estado, 'completed': fin}},
                                         'competitors': [eq(1, gh, 0), eq(2, ga, 0)]}]},
            'boxscore': {'teams': [{'team': {'id': '1'}, 'statistics': [{'name': 'wonCorners', 'displayValue': str(cor[0])},
                                                                       {'name': 'totalShots', 'displayValue': '9'}]},
                                   {'team': {'id': '2'}, 'statistics': [{'name': 'wonCorners', 'displayValue': str(cor[1])},
                                                                       {'name': 'totalShots', 'displayValue': '6'}]}]}}


class Resp:
    def __init__(self, d, ok=True):
        self._d, self.ok, self.status_code = d, ok, 200 if ok else 500

    def json(self):
        return self._d


class Sesion:
    """ESPN, el sitio y Supabase de mentira; apunta lo que se escribe."""
    def __init__(self, esp):
        self.esp, self.post_, self.patch_ = esp, [], []

    def get(self, url, params=None, **kw):
        if url.endswith('hoy.json'):
            return Resp({'picks': [{'partido': 'Alfa vs Beta', 'deporte': 'Fútbol', 'espn': 'soccer/all:1', 'girado': False,
                                    'inicio': self.ini, 'fecha': self.ini[:10], 'liga': 'Liga X',
                                    'ctx': {'sl': {'n': 10, 'gf': 1.6, 'gc': 1.1}, 'sv': {'n': 10, 'gf': 1.2, 'gc': 1.4}}}]})
        if url.endswith('analisis.json'):
            return Resp({'analisis': []})
        if 'espn' in url:
            return Resp(self.esp)
        if 'telegram_enviados' in url:
            return Resp([])
        if 'pulso_ia' in url:
            return Resp(self.recs)
        return Resp({}, ok=False)

    def post(self, url, **kw):
        self.post_.append((url, kw.get('json')))
        return Resp({})

    def patch(self, url, **kw):
        self.patch_.append((kw.get('params'), kw.get('json')))
        return Resp({})


def probar():
    import datetime as dt
    M = json.loads(leer('web', 'pulso_modelo.json'))
    e = pv.estado_vivo(resumen(), False)
    check(e['t'] == 72 and e['g'] == [1, 1] and e['c'] == 7 and e['periodo'] == 2, 'v520: minuto, marcador y córners de ESPN')
    eg = pv.estado_vivo(resumen(gh=2, ga=0, cor=(5, 1)), True)
    check(eg['g'] == [0, 2] and eg['stats']['wonCorners'] == ['1', '5'], 'v520: «girado» voltea marcador y estadísticas')
    ctx = {'sl': {'n': 10, 'gf': 1.6, 'gc': 1.1}, 'sv': {'n': 10, 'gf': 1.2, 'gc': 1.4}}
    f = ph.rasgos(M, ctx, 72.0, 1, 1, 7)
    ms = pv.mercados(M, f)
    check({m['k'] for m in ms} >= {'gol', 'cor1', 'cor2'} and all(m['tramo'] is None or m['tramo']['n'] >= 100 for m in ms),
          'v520: los mercados del Pulso con su tramo medido (100+ casos)')
    b = pv.mejor(ms)
    check(b is not None and 1 / b['p'] >= pv.JUSTA_MIN and b['p'] >= 0.6, 'v520: «mejor» como la página (aún paga 1,15+)')
    fs = ph.rasgos(M, {}, 72.0, 1, 1, 7)
    check(pv.clave_modelo(M, 'gol', fs) == 'gol_sf' and pv.clave_modelo(M, 'gol', f) == 'gol' and pv.clave_modelo(M, 'gol_v', fs) == 'gol_v',
          'v520: sin fuerza previa, la tabla del modelo sin fuerza (el visitante no tiene)')
    p = {'partido': 'Zeta vs alfa', 'deporte': 'Fútbol', 'inicio': '2026-10-30 03:30:00', 'fecha': '2026-10-30'}
    check(pv.clave_partido(p) == 'Fútbol|alfa / zeta|2026-10-29', 'v520: la clave del partido es la de la página (día en CDMX)')
    js = leer('web', 'app.js')
    check("const clavePartido = (p) => [p.deporte || '', lados(p).map((x) => x.toLowerCase().trim()).sort().join(' / '), diaDe(p)].join('|');" in js,
          'v520: la página arma la clave igual (si cambia allá, cambia aquí)')
    rec = {'marcador': '1-1', 'mercado': 'cor2', 'corners': 7}
    check(pv.liquidar(rec, [2, 1], 9) is True and pv.liquidar(rec, [2, 1], 8) is False and pv.liquidar(rec, [2, 1], None) is None,
          'v520: los córners se liquidan con los del pitido')
    check(pv.liquidar(dict(rec, mercado='gol'), [1, 1], 9) is False and pv.liquidar(dict(rec, mercado='gol_v'), [1, 2], 9) is True,
          'v520: los goles se liquidan con el marcador final')
    # una vuelta completa en seco: con 75 %+ sale el aviso; sin la clave de Gemini, sin IA (y no se inventa)
    os.environ.pop('GEMINI_API_KEY', None)
    s = Sesion(resumen(reloj="70'", gh=0, ga=0, cor=(7, 6)))
    s.ini = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=80)).strftime('%Y-%m-%d %H:%M:%S')
    s.recs = []
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = pv.vuelta(s, M, ('https://x/rest/v1/', {}), seco=True)
    check(r['en_juego'] == 1 and r['segundo_tiempo'] == 1 and r['ia'] == 0, 'v520: una vuelta: el partido en el 2.º tiempo, sin IA sin su clave')
    check('Pulso SharPicks · en vivo' in buf.getvalue() and 'salió' in buf.getvalue() and not s.post_,
          'v520: el aviso dice lo medido y en seco no escribe nada')
    # al terminar: se liquida lo recomendado de ese partido
    s2 = Sesion(resumen(estado='post', reloj="90'", gh=1, ga=0, cor=(6, 4), fin=True))
    s2.ini = s.ini
    s2.recs = [{'clave': pv.clave_partido({'partido': 'Alfa vs Beta', 'deporte': 'Fútbol', 'inicio': s.ini}), 'marcador': '0-0',
                'mercado': 'gol', 'corners': 7, 'acierto': None}]
    r2 = pv.vuelta(s2, M, ('https://x/rest/v1/', {}), seco=False)
    check(r2['liquidadas'] == 1 and s2.patch_ and s2.patch_[0][1] == {'acierto': True}, 'v520: al pitido se liquida lo recomendado')
    wf = leer('.github', 'workflows', 'pulso_vivo.yml')
    check('self-hosted' in wf and 'python pulso_vivo.py --minutos' in wf and 'GEMINI_API_KEY' in wf and 'TELEGRAM_CHAT_VIP' in wf,
          'v520: el workflow corre en el PC con Gemini y el canal VIP')
    sq = leer('supabase', 'v520_pulso_ia.sql')
    check('(select public.es_pro())' in sq and 'pulso_desbloqueos d' in sq and 'pulso_ia_tasa' in sq,
          'v520: la recomendación sólo para VIP o con el Pulso abierto; la tasa, para todos')
    check("rpc('pulso_ia_hay'" in leer('web', 'cuenta.js') or "rpc('pulso_ia_hay'" in js, 'v520: la página sabe qué partidos tienen recomendación')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
