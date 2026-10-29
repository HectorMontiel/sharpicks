#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v477 — el parley en todos los partidos que Playdoit cotiza: lo que no viene en mercado_dia.json se
pide a la casa en vivo (sólo el exportador), con sus nombres («PSG», «(F)»), sin confundir el
femenil con el varonil; y sin histórico de la liga, con la probabilidad de la casa sola. Sin red."""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    import escudos
    import errores_web as ew
    import lineas_stats as ls
    check(escudos._cat('', 'Cruz Azul (F)', 'Deportivo Toluca (F)') == (True, False), 'v477: «(F)» de Playdoit es femenil')
    check(ew._limpio('PSG') == 'Paris Saint-Germain' and ew._limpio('Olympique Lyonnais') == 'Lyon' and ew._limpio('Tigres de la UANL (F)') == 'Tigres de la UANL',
          'v477: las abreviaturas de la casa y el «(F)» fuera para emparejar')
    check(ew.RED_CASA is False and "errores_web.RED_CASA = True" in open('exportar_web.py', encoding='utf-8').read(),
          'v477: la casa en vivo sólo se pide en la pasada del exportador (las pruebas y la página no piden red)')
    # el buscador de la casa devuelve el FEMENIL para un partido varonil: se descarta
    cat = {'futbol': {'x': {'home': 'Cruz Azul (F)', 'away': 'Deportivo Toluca (F)', 'liga': 'Liga MX Femenil', 'fecha': '2026-10-25T02:10:00', 'event_id': 1}}}
    viejo = sys.modules.get('cuotas_multi')
    sys.modules['cuotas_multi'] = types.SimpleNamespace(
        mercados_playdoit=lambda dep, h, a, fecha=None, liga=None: {'home': 'Cruz Azul (F)', 'away': 'Deportivo Toluca (F)', 'liga': 'Liga MX Femenil', 'mercados': [1]},
        _indice_pdt=lambda dep: cat['futbol'])
    try:
        ew._CASA_MEM.clear()
        varonil = ew.playdoit_en_vivo('Cruz Azul', 'Toluca', '2026-10-25 02:10:00', 'Liga MX')
    finally:
        if viejo is not None:
            sys.modules['cuotas_multi'] = viejo
        else:
            sys.modules.pop('cuotas_multi', None)
        ew._CASA_MEM.clear()
    check(varonil == {}, 'v477: el varonil NUNCA se queda con el tablero del femenil')
    # el tablero con los bandos al revés se endereza
    g = ew._girar({'corners_home': {'5.5': {}}, 'corners_away': {'3.5': {}}, '1x2': {'home': 0.6, 'draw': 0.2, 'away': 0.2}})
    check(list(g['corners_home']) == ['3.5'] and g['1x2']['home'] == 0.2, 'v477: si la casa lo publica al revés, se endereza')
    # sin histórico de la liga: sólo la casa
    casa = {'goles_home': {'0.5': {'p': 0.78, 'mas': 1.2, 'menos': 4.0}}, 'corners_away': {'2.5': {'p': 0.71, 'mas': 1.3, 'menos': 3.2}},
            '1x2': {'home': 0.55, 'draw': 0.25, 'away': 0.20}, 'doble_cuotas': {'1X': 1.2, 'X2': 2.0, '12': 1.3},
            'goles': {'2.5': {'p': 0.52, 'mas': 1.85, 'menos': 1.95}, '1.5': {'p': 0.76, 'mas': 1.25, 'menos': 3.6}}, 'btts': 0.5, 'btts_cuotas': {'si': 1.9, 'no': 1.9}}
    sc = ls.solo_casa(casa)
    fams = [x[0] for x in sc['par']]
    check(sc and sc['casa'] and len(sc['par']) >= 3 and fams.count('doble') == 1 and not ('goles_total' in fams and 'btts' in fams),
          'v477: sin histórico, el parley con la prob. de la casa y sus mercados principales (una pata por familia): %s' % sc['par'])
    check(any(x[0] == 'doble' and x[1] == '1X' and abs(x[3] - 0.80) < 1e-6 for x in sc['par']), 'v477: doble oportunidad con la prob. del 1X2 de la casa')
    check(ls.solo_casa({}) is None, 'v477: sin casa, nada')
    app = open(os.path.join('web', 'app.js'), encoding='utf-8').read()
    check("st === 'doble' ? 'Doble oportunidad: <b>'" in app and "st === 'btts' ? 'Ambos anotan: <b>'" in app, 'v477: la página nombra las patas nuevas')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
