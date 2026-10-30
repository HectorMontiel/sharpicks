#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v531 — el morado de la IA (sólo VIP): la «confianza» de la IA (1-5 por partido) separa los 💎/🔷/🥇 que sí se
cumplen (5 → 91 % vs 82 %, p5 +5,1; ≥4 → 86 %, p5 +2,5), su «a favor» no. Destacados, Para ti y las patas del armador.
Sin red."""
import io
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    app = io.open(os.path.join(AQUI, 'web', 'app.js'), encoding='utf-8').read()
    check("if (!window.SPX || !SPX.esVip || !SPX.esVip() || !p || p.tipo === 'error') return 0;" in app,
          'v531: el morado es sólo para el VIP')
    check("if (!['diamante', 'platino', 'oro'].includes(nivel(p).c)) return 0;" in app and 'return c >= 5 ? 2 : c >= 4 ? 1 : 0;' in app,
          'v531: sólo 💎/🔷/🥇 (en Plata la IA no separa), con la confianza 5 y 4 medidas')
    check("const IA_SALIO = { 2: 0.91, 1: 0.86 };" in app and "' IA: mayor probabilidad'" in app,
          'v531: el sello dice lo que de verdad salió («mayor probabilidad · salió 91 %»)')
    check("(ia ? ' ia-' + ia : '')" in app and "porIA(dest, (g) => g[0])" in app and "porIA(pt, (g) => g[0])" in app,
          'v531: Destacados y Para ti en morado, primero los que la IA ve mejor')
    check("if (estado.arm.soloIA && !iaSegura(p)) continue;" in app and 'data-arm-soloia' in app and "' · con la IA ~<b>'" in app,
          'v531: el armador marca cada pata, cuenta las seguras, arma sólo con ellas y da la probabilidad con la IA')
    css = io.open(os.path.join(AQUI, 'web', 'estilo.css'), encoding='utf-8').read()
    check('.dest.ia-2, .arm-pata.ia-2' in css and '.ia-sello' in css, 'v531: el morado en el estilo')
    cu = io.open(os.path.join(AQUI, 'web', 'cuenta.js'), encoding='utf-8').read()
    check("sb.rpc('ia_morado_tasa')" in cu and 'function moradoHist()' in cu and "'Más difícil'" not in app,
          'v531: el morado se mide en el historial; sin morado no se pone nada')

    ia = io.open(os.path.join(AQUI, 'ia_gemini.py'), encoding='utf-8').read()
    check('web = noticias_rss(lote)' in ia and 'web = noticias_web(lote' not in ia,
          'v533: sólo Google News (la búsqueda de Gemini nunca respondió), en todos los deportes')
    check("if nombre == 'v2' and k:" in ia and "json={'mejor_2h': x['mejor_apuesta']" in ia and "a.mejor_2h ?" in app,
          'v533: la mejor jugada de 2 h antes se enseña (columnas aparte; la medición principal no se toca)')

if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
