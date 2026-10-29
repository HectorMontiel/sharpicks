#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v486 — el reloj en vivo: en el descanso dice «Medio tiempo» (ESPN deja congelado «45'+3'»), y en el
tiempo agregado enseña el minuto exacto y cuántos minutos agregó el árbitro (FotMob). Sin red."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    app = open(os.path.join(AQUI, 'web', 'app.js'), encoding='utf-8').read()
    css = open(os.path.join(AQUI, 'web', 'estilo.css'), encoding='utf-8').read()
    check('function relojVivo(v, p)' in app and "if (enPausa(v)) return { t: 'Medio tiempo', sub: '' };" in app,
          'v486: en el descanso el reloj dice «Medio tiempo»')
    check("const PAUSA_RE = /medio|descanso|half|^ht$|et-ht|pausa/i;" in app and 'const pausa = !v || v.fase !== \'in\' || enPausa(v);' in app,
          'v486: la cancha y el reloj usan la misma regla de pausa')
    check("/^(\\d+)'?\\s*\\+\\s*(\\d+)'?$/" in app and "minuto: base + extra, agregado: deC" in app,
          'v486: «45\'+3\'» se lee como minuto 48 (3.º de la compensación)')
    check("(base <= 45 ? c.tiempo === 1 : c.tiempo === 2)" in app and "'de +' + deC" in app,
          'v486: los minutos agregados (FotMob) sólo del tiempo que se está jugando')
    f = app[app.index('function relojFila(ps)'):][:700]
    check('relojVivo(v, ps[0])' in f and 'rl-comp' in f, 'v486: la fila usa el reloj nuevo')
    e = app[app.index('function etiquetaEstado(p, v)'):][:900]
    check("' (minuto ' + rv.minuto + ')'" in e and "' de compensación'" in e, 'v486: la cabecera dice el minuto exacto y la compensación')
    check("/\\+/.test(String(v.reloj || ''))" in app and 'presionFM(p).catch(() => false)' in app,
          'v486: en tiempo agregado se pide la compensación aunque la tarjeta esté cerrada')
    check('.rl.vivo .rl-comp' in css, 'v486: «de +4» debajo del reloj')
    # v487 — los goles de la presión: la fuente que cuadra con el marcador
    check("fuentesGol.find((f) => totalGoles != null && f.length === totalGoles)" in app
          and "const golesE = evE.filter((e) => e.gol)" in app,
          'v487: los balones de la presión salen de la fuente cuyos goles cuadran con el marcador')
    pr = open(os.path.join(AQUI, 'functions', 'presion.js'), encoding='utf-8').read()
    check("const lt = ((((det && det.header) || {}).status || {}).liveTime) || st.liveTime || {};" in pr,
          'v488: la compensación sale del detalle del partido (30 s), no de la lista del día (10 min)')
    check("const fm = estado.pfm[clavePartido(p)] || {};" in app and "suma((fm.todo || {}).amarillas)" in app
          and "fm.eventos.filter((e) => e.tipo !== 'gol').length" in app,
          'v489: tarjetas y córners del «cómo va» con la cuenta más alta de las fuentes (ESPN iba atrasado)')
    check("minuto: Number(g.gameTime) > 0 ? Number(g.gameTime) : null, minutoTxt: g.gameTimeDisplay || ''" in app
          and "d3 && d3.minutoTxt) return { t: d3.minutoTxt, sub: '' };" in app,
          'v489: sin minuto (sólo Flashscore, «2.ª parte») se usa el de 365Scores')
    check(r"const reloj = /\d+\s*['’]|^\d+$/.test(relojTxt)" in app, 'v489: «2.ª parte» ya no se lee como minuto 2')
    # v490 — tocar el escudo abría el filtro de deportes («Todos»): la imagen llevaba `data-dep`
    esc_fn = app[app.index('function escudo(url, nombre, dep)'):][:300]
    check('data-dep=' not in esc_fn and 'data-silueta=' in esc_fn, 'v490: el escudo ya no se confunde con el filtro de deportes')
    check("linea: 'Sin datos de presión en esta liga'" in app, 'v489: sin datos de presión, se dice')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
