#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v484 — la equis blanca que borra la búsqueda de un toque, y en «Por hora» los partidos sin pick en un
bloque plegado que se abre al tocarlo (como las ligas). Sin red."""
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
    app, html, css = leer('web', 'app.js'), leer('web', 'index.html'), leer('web', 'estilo.css')
    check('id="busca"' in html and 'id="busca-x" aria-label="Borrar la búsqueda" hidden>×</button>' in html,
          'v484: la equis está junto al buscador y empieza escondida')
    check("$('busca-x').hidden = !v" in app and "$('busca').value = ''; $('busca-x').hidden = true; estado.busca = ''; pintar();" in app,
          'v484: aparece al escribir y borra todo de un toque')
    check('.busca-x {' in css and 'color: #fff' in css and '::-webkit-search-cancel-button' in css,
          'v484: equis blanca (y sin la del navegador encima)')
    check('const sinPick = (g) => g.every((x) => x.solo_analisis)' in app and 'data-ver-sinpick' in app
          and "estado.verSinPick = !estado.verSinPick" in app,
          'v484: en «Por hora» los sin pick van en un bloque que se abre y se cierra')
    check('estado.verSinPick = false;' in app and "(estado.verSinPick ? '<section class=\"liga-bloque por-hora\">'" in app,
          'v484: el bloque empieza plegado y sólo se pinta abierto')
    check("[data-ver-fin],[data-ver-sinpick],[data-ord]" in app, 'v484: el toque al bloque se atiende')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
