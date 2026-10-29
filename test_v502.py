#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v501 — Destacados terminados con su marcador final y Verde/Roja. v502 — el día de ESPN que no contesta
se reintenta (la Brasileirão de mañana se perdía entera por un fallo suelto) y la Carabao entra como las
otras copas (ELO común con sus ligas, sólo análisis, penales sin prórroga). Sin red."""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


class R:
    def __init__(self, ev, code=200):
        self._ev, self.status_code = ev, code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP %s' % self.status_code)

    def json(self):
        return {'events': self._ev}


def probar_reintento():
    import fixtures_espn as fe
    llamadas = {}

    def get(url, params=None, timeout=None, headers=None):
        d = params['dates']
        llamadas[d] = llamadas.get(d, 0) + 1
        if d == '20261029' and llamadas[d] == 1:        # el día de los clásicos falla la 1.ª vez
            raise TimeoutError('ESPN no contestó')
        return R([{'id': d + '-1', 'date': '%s-%s-%sT22:30Z' % (d[:4], d[4:6], d[6:])}])
    viejo, vsleep = fe.requests.get, None
    import time
    vsleep = time.sleep
    fe.requests.get, time.sleep = get, (lambda s: None)
    try:
        ev = fe.eventos_por_dias('prueba', 'https://x', '20261028', '20261030')
    finally:
        fe.requests.get, time.sleep = viejo, vsleep
    check(ev is not None and len(ev) == 3 and llamadas.get('20261029') == 2,
          'v502: el día que no contesta se pide otra vez y sus partidos llegan (%s)' % llamadas)


def probar_carabao():
    import config
    import uefa_scraper as us
    c = config.LEAGUES.get('eng_carabao') or {}
    check(c.get('disponible') and c.get('solo_analisis') and 'premier' in (c.get('agrupar_con') or []),
          'v502: la Carabao encendida, con sus ligas (ELO común) y sólo análisis hasta medirla')
    check('eng.league_cup' in us.PENALES_SIN_PRORROGA, 'v502: en la Carabao el empate va a penales sin prórroga: entra al entreno')
    import exportar_web as ew
    check('eng_carabao' in ew._ligas_solo_analisis(), 'v502: sus picks no cuentan hasta medirlos (como la Pokal y la Copa del Rey)')


def probar_destacados():
    app = open(os.path.join(AQUI, 'web', 'app.js'), encoding='utf-8').read()
    d = app[app.index('function destacado(ps, etiqueta)'):][:1600]
    check("const gm = /^\\s*(\\d+)\\s*-\\s*(\\d+)\\s*$/.exec(String(p.marcador || ''));" in d and "gm ? gm[1] + ' - ' + gm[2]" in d,
          'v501: terminado, el Destacado enseña el marcador final')
    check("ev === 'verde' ? '<span class=\"ok res\">' + OK() + ' Verde</span>'" in d and "(res || '<span>probabilidad '" in d,
          'v501: y si fue verde o roja')


def probar_fuga_copas():
    """v504 — un pick de copa que ya empezó llegaba sin liga, pasaba el filtro y contaba."""
    import exportar_web as ew
    solo = ew._ligas_solo_analisis()
    crudo = {'partido': 'Bayern Munich vs Magdeburg', 'fecha': '2026-10-28', 'apuesta': 'Goles: Menos de 6.5', 'deporte': 'Fútbol'}
    f = ew._fila(crudo, 'vivo', {'Bayern Munich vs Magdeburg': 'DFB-Pokal'})
    check(ew._cuenta(crudo, solo) and not ew._cuenta(f, solo), 'v504: sin liga pasaba; ya con su liga (la que pone _fila) se queda fuera')
    src = open(os.path.join(AQUI, 'exportar_web.py'), encoding='utf-8').read()
    check(src.count('if _cuenta(f, solo)]') == 3, 'v504: las tres listas (jugadas, próximas, cuota alta) filtran la fila ya hecha')


if __name__ == '__main__':
    probar_fuga_copas()
    probar_reintento()
    probar_carabao()
    probar_destacados()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
