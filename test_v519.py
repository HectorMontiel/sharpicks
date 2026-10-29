#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v519 — en los runners propios (PC) la carpeta del repo se REUSA entre workflows: un checkout parcial
(sparse-checkout) deja su configuración guardada y el siguiente workflow ve el repo casi vacío (29-oct: Sitio
web y Precálculo fallaron con «no requirements.txt»). Ningún workflow puede volver a usarlo. Sin red."""
import glob
import io
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    wfs = sorted(glob.glob(os.path.join(AQUI, '.github', 'workflows', '*.yml')))
    check(len(wfs) >= 10, 'se leyeron los workflows (%d)' % len(wfs))
    for f in wfs:
        s = io.open(f, encoding='utf-8').read()
        n = os.path.basename(f)
        lineas = [l for l in s.splitlines() if not l.strip().startswith('#')]
        check(not any('sparse-checkout' in l for l in lineas), 'v519: %s sin checkout parcial (envenena la carpeta del runner)' % n)
        if 'self-hosted' in s and 'pip install -r requirements.txt' in s:
            check('pip install --force-reinstall' in s, 'v516: %s repara solo una instalación de pip cortada' % n)


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
