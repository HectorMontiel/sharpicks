#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v481 — el tenista sin foto lleva la bandera de su país (Flashscore da el país; foto no hay para casi
ningún juvenil ITF). «World» (neutral) sigue con la silueta. Sin red."""
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
    import resultados_flashscore as rf
    feed = 'x'
    regs = [{'AA': '1', 'AE': 'Shao Y.', 'AF': 'Yang A.', 'FU': 'China', 'FV': 'World'},
            {'AA': '2', 'AE': 'Lin Y. J./Shao Y.', 'AF': 'Huang Y./Zelinskaya D.', 'FU': 'China', 'FV': 'Russia'}]
    viejo_get, viejo_reg = escudos.__dict__.get('requests'), rf._registros
    import requests
    viejo_rget = requests.get
    requests.get = lambda *a, **k: types.SimpleNamespace(text=feed)
    rf._registros = lambda t: regs
    filas = [{'deporte': 'Tenis', 'partido': 'Anna Yang vs Yushan Shao', 'logo_h': None, 'logo_a': None},
             {'deporte': 'Tenis', 'partido': 'Jannik Sinner vs Otro Jugador', 'logo_h': 'https://foto/sinner.png', 'logo_a': None},
             {'deporte': 'Fútbol', 'partido': 'A vs B', 'logo_h': None, 'logo_a': None}]
    try:
        n = escudos.banderas_tenis(filas, dias=(0,))
    finally:
        requests.get, rf._registros = viejo_rget, viejo_reg
    check(filas[0]['logo_a'] == 'https://flagcdn.com/w80/cn.png' and filas[0]['logo_h'] is None and n == 1,
          'v481: la bandera del país al que no tiene foto, con los lados enderezados; «World» sin bandera')
    check(filas[1]['logo_h'] == 'https://foto/sinner.png' and filas[2]['logo_h'] is None,
          'v481: la foto real no se pisa y el fútbol no se toca')
    check(all(len(v) == 2 and v.islower() for v in escudos.PAIS_ISO.values()) and 'World' not in escudos.PAIS_ISO,
          'v481: la tabla de países da códigos ISO de dos letras y no tiene «World»')
    css = open(os.path.join('web', 'estilo.css'), encoding='utf-8').read()
    check('.escudo[src*="flagcdn.com"]' in css, 'v481: la bandera se pinta redonda, no estirada')
    src = open('escudos.py', encoding='utf-8').read()
    check("st['banderas'] = banderas_tenis(filas)" in src, 'v481: `poner` la aplica después de buscar la foto')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
