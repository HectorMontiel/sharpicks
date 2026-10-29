#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v503 — prórroga y penales: el estado de ESPN con su nombre (no «Final» a media prórroga), la tanda tiro
por tiro y, sin dato en vivo, una copa no se da por terminada a las 2 h. Sin red."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    with open(os.path.join(AQUI, 'web', 'app.js'), encoding='utf-8') as fh:
        app = fh.read()
    with open(os.path.join(AQUI, 'web', 'estilo.css'), encoding='utf-8') as fh:
        css = fh.read()
    for est in ('STATUS_END_OF_REGULATION', 'STATUS_HALFTIME_ET', 'STATUS_END_OF_EXTRATIME', 'STATUS_SHOOTOUT', 'STATUS_FINAL_PEN', 'STATUS_FINAL_AET'):
        check(est + ':' in app, 'v503: %s tiene nombre en español' % est)
    check("est: st.name || '', pen: penalesDe(d, comp, nos1)," in app and 'Array.isArray(d.shootout)' in app,
          'v503: se lee la tanda de ESPN (cada tiro, jugador y si entró)')
    check("if (v.est === 'STATUS_SHOOTOUT' || v.est === 'STATUS_END_OF_EXTRATIME') return { t: 'Penales', sub: pen };" in app,
          'v503: el reloj dice «Penales» con la tanda debajo')
    check("function penalesHtml(v, L, V)" in app and app.count('penalesHtml(v, L, V)') >= 3, 'v503: la tanda en la tarjeta y en la ficha')
    check("duracion(ps[0].deporte) * (copa ? 1.45 : 1)" in app, 'v503: sin dato en vivo, una copa no se da por terminada a las 2 h')
    check("sort((a, b) => (!!estado.vivo[a[0]]) - (!!estado.vivo[b[0]]))" in app, 'v503: primero se piden los que aún no tienen dato')
    check('.pen-t .pen-si' in css and '.pen-t .pen-no' in css, 'v503: círculos verde/rojo por tiro')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
