#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v494 — la guía interactiva de la app: breve (7 pasos), Siguiente / Omitir, sale sola la primera vez y se
repite desde la ayuda. Sin red."""
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*p):
    with open(os.path.join(AQUI, *p), encoding='utf-8') as fh:
        return fh.read()


def probar():
    g, html, css, wf = leer('web', 'guia.js'), leer('web', 'index.html'), leer('web', 'estilo.css'), leer('.github', 'workflows', 'sitio_web.yml')
    pasos = re.findall(r"\{ v: '(\w+)', sel: [^}]+, t: '([^']+)', d: '([^']+)' \}", g)
    check(8 <= len(pasos) <= 15, 'v494: la guía es breve (%d pasos)' % len(pasos))
    check({v for v, _, _ in pasos} >= {'picks', 'vivo', 'combinadas', 'mios', 'historial', 'planes'},
          'v495: UNA guía que recorre todas las secciones')
    check("if (await irA(PASOS[n].v))" in g and "irA(desde);" in g, 'v495: cambia de pantalla ella misma y al final vuelve')
    check("No volver a mostrar la guía</label>" in g and "if (nunca) localStorage.setItem(NUNCA, '1')" in g
          and "!!localStorage.getItem(NUNCA)" in g, 'v495: casilla «No volver a mostrar»')
    check(all(len(d) <= 110 for _, _, d in pasos), 'v494: cada paso se explica en una línea corta')
    check("'Siguiente'" in g and "'Omitir'" in g and "'Listo'" in g, 'v494: botones Siguiente, Omitir y Listo')
    check("function yaVista() { try { return !!localStorage.getItem(NUNCA); }" in g and 'try {' in g,
          'v498: sale cada vez que se abre la app hasta marcar «No volver a mostrar» (y sin almacenamiento no truena)')
    check("if (!PASOS[n].sel || objetivo(PASOS[n])) break;" in g, 'v494: si una parte no está a la vista, el paso se salta')
    check("class=\"guia-atras\">Atrás</button>" in g and "paso(i - 1, -1)" in g, 'v540: botón Atrás')
    check("if (ocupado) { pendiente = [n, dir]; return; }" in g, 'v540: un toque mientras cambia de pantalla no se pierde')
    check('<script src="guia.js"></script>' in html and 'data-guia>▶ Ver la guía de la app</button>' in html,
          'v494: se carga en la página y se repite desde la ayuda')
    check('.guia-luz {' in css and '.guia-caja {' in css, 'v494: la luz y la ventanita')
    check('node --check web/guia.js' in wf, 'v494: el despliegue valida guia.js')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
