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
        # v523 — el repo es público: un runner propio en un repo público deja correr código ajeno en el PC del
        # usuario, y además el usuario no quiere depender de su compu encendida
        check('self-hosted' not in ''.join(lineas), 'v523: %s corre en los servidores de GitHub, no en el PC' % n)
        if 'self-hosted' in s and 'pip install -r requirements.txt' in s:
            check('pip install --force-reinstall' in s, 'v516: %s repara solo una instalación de pip cortada' % n)

    # v537 — el repo es PÚBLICO: ningún enlace privado de Telegram (t.me/+…) en el código; el del VIP lo da la app
    import re
    import subprocess
    archivos = subprocess.run(['git', 'ls-files', '*.py', '*.js', '*.html', '*.yml', '*.md', '*.sql', '*.json'], cwd=AQUI,
                              capture_output=True, text=True).stdout.split()
    malos = [f for f in archivos if not f.startswith('.validacion') and os.path.exists(os.path.join(AQUI, f))
             and re.search(r't\.me/\+[A-Za-z0-9_-]{8,}', io.open(os.path.join(AQUI, f), encoding='utf-8', errors='ignore').read())]
    check(not malos, 'v537: ningún enlace privado de Telegram en el repo público (%s)' % ', '.join(malos[:5]))

if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
