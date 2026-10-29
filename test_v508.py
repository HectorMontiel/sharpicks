#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v508 — auditoría de seguridad: id del pick con HMAC (no se adivina el pick de pago), escapado con comilla
simple, workflows con permisos mínimos y sin inyección, firma del respaldo y la migración. Sin red."""
import hashlib
import io
import os

import exportar_web as ew

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(r):
    with io.open(os.path.join(AQUI, r), encoding='utf-8') as fh:
        return fh.read()


def probar():
    p = {'fecha': '2026-10-28', 'partido': 'Inter Miami vs FC Cincinnati', 'apuesta': 'Inter Miami o empate'}
    viejo = hashlib.sha1(b'2026-10-28|Inter Miami vs FC Cincinnati|Inter Miami o empate').hexdigest()[:20]
    guardado = {k: os.environ.get(k) for k in ('PICK_ID_CLAVE', 'GITHUB_ACTIONS', 'SUPABASE_SERVICE_KEY')}
    try:
        os.environ['PICK_ID_CLAVE'] = 'clave-de-prueba'
        a = ew._id(p)
        check(a != viejo and len(a) == 20, 'v508: con clave el id ya no es el sha1 adivinable')
        check(ew._id(dict(p, apuesta='🏆 ⭐ Inter Miami o empate')) == a, 'v508: las marcas siguen sin cambiar el id')
        os.environ['PICK_ID_CLAVE'] = 'otra'
        check(ew._id(p) != a, 'v508: otra clave, otro id (sin la clave no se reproduce)')
        os.environ.pop('PICK_ID_CLAVE')
        os.environ.update(GITHUB_ACTIONS='true', SUPABASE_SERVICE_KEY='x')
        try:
            ew._id(p)
            check(False, 'v508: publicando sin clave se para (nunca sube ids adivinables)')
        except RuntimeError:
            check(True, 'v508: publicando sin clave se para (nunca sube ids adivinables)')
    finally:
        for k, v in guardado.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    sw = leer('.github/workflows/sitio_web.yml')
    check('PICK_ID_CLAVE: ${{ secrets.PICK_ID_CLAVE }}' in sw, 'v508: el sitio publica con la clave del id')
    for f in ('web/app.js', 'web/cuenta.js'):
        check('''"'": '&#39;' ''' in leer(f), 'v508: %s escapa también la comilla simple' % f)
    for f in ('telegram_bot', 'telegram_dia_completo', 'test_instalacion_limpia', 'test_sharpicks_v402', 'validate_sharpicks'):
        check('permissions:\n  contents: read' in leer('.github/workflows/%s.yml' % f), 'v508: %s con permisos de lectura' % f)
    # v509 — GitHub rechaza un workflow con una clave repetida («No jobs were run»); yaml.safe_load no avisa
    import re
    for f in sorted(os.listdir(os.path.join(AQUI, '.github', 'workflows'))):
        if f.endswith('.yml'):
            raiz = re.findall(r'(?m)^([A-Za-z_][\w-]*):', leer('.github/workflows/' + f))
            check(len(raiz) == len(set(raiz)), 'v509: %s sin claves repetidas arriba (%s)' % (f, ','.join(raiz)))
    ros = leer('.github/workflows/precalcular_rosters.yml')
    check('LIGAS: ${{ github.event.inputs.ligas }}' in ros and '\n                 ${{ github.event.inputs.ligas }}' not in ros,
          'v508: la entrada «ligas» va por variable (sin inyección de comandos)')
    rb = leer('.github/workflows/respaldo_base.yml')
    check('.tgz.enc.hmac' in rb and 'hmac.new' in rb, 'v508: el respaldo lleva firma HMAC')
    sq = leer('supabase/v508_seguridad.sql')
    check("'demasiados intentos'" in sq and 'codigos_intentos' in sq, 'v508: canjear códigos con límite de intentos')
    check('revoke insert, update, delete' in sq and "grant update (usuario, nombre, deportes, ligas) on public.perfiles" in sq,
          'v508: sin permisos de escritura de más')
    check("'demasiados intentos'" in leer('web/cuenta.js'), 'v508: la página explica el límite de intentos')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
