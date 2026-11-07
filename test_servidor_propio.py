#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rama servidor-propio: los flujos sólo cambian al encender RUNNER_PESADO, y lo público sigue en GitHub."""
import glob
import os

import yaml

_fallos = []


def ok(nombre, cond):
    print(('OK   ' if cond else 'FALLA') + ' ' + nombre)
    if not cond:
        _fallos.append(nombre)


MOVIDOS = {'cuotas_mx', 'precalcular_rosters', 'precalculo_dia', 'radar_diario', 'recalibrar', 'relevo', 'respaldo_base',
           'retrain_leagues', 'sitio_web', 'telegram_bot', 'telegram_dia_completo', 'vigia_limites'}
CON_FOTO = MOVIDOS - {'relevo', 'respaldo_base', 'vigia_limites'}
VARIABLE = "${{ vars.RUNNER_PESADO || 'ubuntu-latest' }}"

for ruta in sorted(glob.glob('.github/workflows/*.yml')):
    nombre = os.path.basename(ruta)[:-4]
    d = yaml.safe_load(open(ruta, encoding='utf-8'))
    disparos = d.get(True) or d.get('on')
    disparos = list(disparos) if isinstance(disparos, dict) else [disparos]
    trabajos = d['jobs'].values()
    if nombre in MOVIDOS:
        ok('%s: sólo con la variable va al servidor' % nombre, all(j.get('runs-on') == VARIABLE for j in trabajos))
        ok('%s: no lo disparan pull requests' % nombre, 'pull_request' not in disparos and 'pull_request_target' not in disparos)
    elif nombre != 'prueba_servidor':
        ok('%s: sigue en GitHub' % nombre, all(j.get('runs-on') == 'ubuntu-latest' for j in trabajos))
    if nombre in CON_FOTO:
        pasos = [p for j in trabajos for p in j.get('steps', [])]
        idx = [i for i, p in enumerate(pasos) if p.get('name') == 'Bajar la foto de precios']
        dep = [i for i, p in enumerate(pasos) if 'dependencias' in str(p.get('name')).lower()]
        ok('%s: baja la foto tras instalar y sólo en el servidor' % nombre, len(idx) == 1 and dep and dep[0] < idx[0] and 'RUNNER_PESADO' in str(pasos[idx[0]].get('if')))

foto = yaml.safe_load(open('.github/workflows/foto_precios.yml', encoding='utf-8'))
ok('la foto nunca va al servidor: desde ahí esas fuentes dan 403', all(j.get('runs-on') == 'ubuntu-latest' for j in foto['jobs'].values()))
ok('el despertador la lanza', 'foto_precios.yml' in open('tools/vps_runner/despertador.sh', encoding='utf-8').read())

print('\n%d fallos' % len(_fallos))
raise SystemExit(1 if _fallos else 0)
