#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v520-v521 — el vigilante del Pulso (avisos VIP e «IA + modelo») corre EN LA NUBE: la función de Supabase
`pulso-vivo`, llamada por pg_cron cada 2 min (no en el PC del usuario). Aquí, sin red: que la función use los mismos
topes, rangos y clave de partido que la página, que la IA sólo elija entre los mercados medidos, que las claves
vivan en Vault y que nada del PC la dispare. La cuenta número por número contra la página la compara
D:/Claude/herramientas/verificar_pulso_nube.py (en línea)."""
import glob
import io
import os
import re

import pulso_historial as ph

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
    ts = leer('supabase', 'functions', 'pulso-vivo', 'index.ts')
    js = leer('web', 'pulso.js')
    app = leer('web', 'app.js')
    check("const TOPE: Record<string, number> = { gol: 0.85, gol2: 0.5, gol_l: 0.75, gol_v: 0.65 };" in ts
          and "const TOPE = { gol: 0.85, gol2: 0.5, gol_l: 0.75, gol_v: 0.65 };" in js, 'v521: los mismos topes en la nube y en la página')
    check("const TOPE_SF: Record<string, number> = { gol: 0.8, gol2: 0.45, gol_l: 0.7 };" in ts and ph.TOPE_SF == {'gol': 0.8, 'gol2': 0.45, 'gol_l': 0.7},
          'v521: los mismos topes sin fuerza previa')
    for n in ('HASTA', 'DESDE'):
        a = re.search(r'const %s(?:: Record<string, number>)? = (\{[^}]+\});' % n, ts).group(1)
        b = re.search(r'const %s = (\{[^}]+\});' % n, js).group(1)
        check(a == b, 'v521: %s igual en la nube y en la página' % n)
    check("lados(p).map((x) => x.toLowerCase().trim()).sort().join(' / ')" in ts
          and "const clavePartido = (p) => [p.deporte || '', lados(p).map((x) => x.toLowerCase().trim()).sort().join(' / '), diaDe(p)].join('|');" in app,
          'v521: la clave del partido es la de la página (y la de los desbloqueos)')
    check('const AVISO_MIN = 0.75, CANDIDATO_MIN = 0.70, JUSTA_MIN = 1.15;' in ts and 'avisados.has(pick)' in ts and "tipo: 'pulso'" in ts,
          'v520: aviso a lo de 75 %+, una vez por partido y mercado')
    check("enum: claves" in ts and 'opciones.find((x) => x.k === r.mercado)' in ts, 'v520: la IA sólo elige entre los mercados medidos')
    check("req.headers.get('x-pulso-clave') !== s.pulso_cron" in ts, 'v521: sólo pg_cron (con su clave de Vault) dispara la función')
    check('rpc/leer_secretos_pulso' in ts and 'Deno.env.get(\'TELEGRAM' not in ts, 'v521: Telegram y Gemini salen de Vault, no del código')
    sq = leer('supabase', 'v521_pulso_nube.sql')
    check("cron.schedule('pulso-vivo', '*/2 * * * *'" in sq and 'grant execute on function public.leer_secretos_pulso() to service_role' in sq
          and "revoke all on function public.guardar_secreto(text, text) from public, anon, authenticated" in sq,
          'v521: cada 2 min en la nube; las claves sólo con la llave de servicio')
    sq0 = leer('supabase', 'v520_pulso_ia.sql')
    check('(select public.es_pro())' in sq0 and 'pulso_desbloqueos d' in sq0 and 'pulso_ia_tasa' in sq0,
          'v520: la recomendación sólo para VIP o con el Pulso abierto; la tasa, para todos')
    wfs = ''.join(leer('.github', 'workflows', os.path.basename(f)) for f in glob.glob(os.path.join(AQUI, '.github', 'workflows', '*.yml')))
    check('pulso_vivo' not in wfs and not os.path.exists(os.path.join(AQUI, 'pulso_vivo.py')),
          'v521: el vigilante ya no corre en el PC (ni workflow ni script)')
    check("rpc('guardar_secreto'" not in wfs and 'rpc/guardar_secreto' in leer('.github', 'workflows', 'claves_supabase.yml'),
          'v521: las claves pasan de GitHub a Vault con el workflow «Claves a Supabase»')
    cu = leer('web', 'cuenta.js')
    check("rpc('pulso_ia_hay'" in cu and "from('pulso_ia')" in cu and "rpc('pulso_ia_tasa')" in cu and 'function iaPulso(p, v)' in app,
          'v520: la página destaca la recomendación y enseña su tasa')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
