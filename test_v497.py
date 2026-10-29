#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v497 — respaldo nocturno: todas las tablas (por páginas de 1000) y las cuentas, empacado y cifrado antes
de guardarse; un respaldo vacío es un fallo. Sin red."""
import json
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


class R:
    def __init__(self, d, code=200):
        self._d, self.status_code, self.ok, self.text = d, code, code < 400, ''

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


def probar():
    import requests
    import respaldo_base as rb
    picks = [{'id': str(i)} for i in range(2350)]

    def get(u, headers=None, params=None, timeout=None):
        if u.endswith('/rest/v1/'):
            return R({'definitions': {'picks': {}, 'perfiles': {}}, 'paths': {'/picks': {}, '/perfiles': {}, '/rpc/x': {}}})
        a, b = [int(x) for x in headers['Range'].split('-')]
        datos = picks if u.endswith('/picks') else [{'id': 'u1'}]
        return R(datos[a:b + 1], 206)
    viejo_g, viejo_p = requests.get, requests.post
    requests.get = get
    requests.post = lambda u, **k: R({'users': [{'id': 'u1', 'email': 'a@b.c'}], 'identities': []})
    try:
        d = tempfile.mkdtemp()
        res = rb.respaldar('https://x.supabase.co', 'k', d)
    finally:
        requests.get, requests.post = viejo_g, viejo_p
    check(res['tablas'] == {'perfiles': 1, 'picks': 2350}, 'v497: todas las tablas, por páginas (2350 picks = 3 páginas)')
    check(res['cuentas'] == 1 and os.path.exists(os.path.join(d, '_auth.json')), 'v497: las cuentas también')
    with open(os.path.join(d, 'picks.json'), encoding='utf-8') as fh:
        check(len(json.load(fh)) == 2350, 'v497: el archivo de la tabla trae todas sus filas')
    wf = open(os.path.join(AQUI, '.github', 'workflows', 'respaldo_base.yml'), encoding='utf-8').read()
    check("openssl enc -aes-256-cbc -pbkdf2" in wf and 'rm -rf respaldo "$F.tgz"' in wf and 'retention-days: 30' in wf,
          'v497: se cifra y lo no cifrado nunca se sube')
    check("cron: '15 9 * * *'" in wf and "workflows: ['Reentrenar modelos de ligas (datos frescos)']" in wf,
          'v497: cada noche (y de respaldo, al terminar el reentrenamiento)')
    sql = open(os.path.join(AQUI, 'supabase', 'v497_respaldo.sql'), encoding='utf-8').read()
    check('revoke all on function public.respaldo_auth() from public, anon, authenticated;' in sql
          and 'grant execute on function public.respaldo_auth() to service_role;' in sql, 'v497: las cuentas sólo con la clave de servicio')
    src = open(os.path.join(AQUI, 'respaldo_base.py'), encoding='utf-8').read()
    check("if not res['tablas'] or not res['tablas'].get('picks') or not res['cuentas']:" in src, 'v497: un respaldo vacío sale en rojo')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
