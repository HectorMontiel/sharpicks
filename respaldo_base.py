# -*- coding: utf-8 -*-
"""
v497 — RESPALDO NOCTURNO DE LA BASE (Supabase, plan gratis: sin respaldos propios).

El usuario: «sí, quiero que se haga ese backup free automático cada noche». Lo corre
`.github/workflows/respaldo_base.yml`. Con la clave de servicio (ya es secreto del repositorio):

  · todas las tablas de `public` (la lista sale del OpenAPI de PostgREST), por páginas de 1000 (v466:
    Supabase corta en 1000 filas);
  · las cuentas (`auth.users` y `auth.identities`) con `public.respaldo_auth()` (sólo service_role).

Escribe `respaldo/AAAA-MM-DD/<tabla>.json` + `resumen.json` (filas por tabla). El workflow lo empaca y
lo CIFRA (AES-256, clave en el secreto RESPALDO_CLAVE) antes de guardarlo: el repositorio es público y
esto lleva correos y los textos premium. La estructura (tablas, funciones, RLS) está en `supabase/*.sql`.

Restaurar: `python respaldo_base.py --restaurar <carpeta>` sube cada tabla con upsert. Las cuentas
(`_auth.json`) van primero y aparte, por SQL en el editor de Supabase (insert en auth.users y
auth.identities con las mismas columnas), porque PostgREST no deja escribir en `auth`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Dict, List

PAGINA = 1000


def _hdr(key: str, extra: Dict = None) -> Dict:
    h = {'apikey': key, 'Authorization': 'Bearer ' + key}
    h.update(extra or {})
    return h


def tablas(url: str, key: str) -> List[str]:
    import requests
    r = requests.get(url.rstrip('/') + '/rest/v1/', headers=_hdr(key, {'Accept': 'application/openapi+json'}), timeout=60)
    r.raise_for_status()
    defs = (r.json().get('definitions') or {})
    paths = r.json().get('paths') or {}
    # sólo tablas y vistas que se pueden leer (no los /rpc/…); las vistas se guardan también, no estorban
    return sorted(k for k in defs if '/' + k in paths)


def bajar(url: str, key: str, tabla: str) -> List[Dict]:
    import requests
    filas, a = [], 0
    while True:
        r = requests.get(url.rstrip('/') + '/rest/v1/' + tabla, headers=_hdr(key, {'Range-Unit': 'items', 'Range': '%d-%d' % (a, a + PAGINA - 1)}),
                         params={'select': '*'}, timeout=120)
        if r.status_code not in (200, 206):
            raise RuntimeError('%s: HTTP %s %s' % (tabla, r.status_code, r.text[:200]))
        lote = r.json()
        filas += lote
        if len(lote) < PAGINA:
            return filas
        a += PAGINA


def respaldar(url: str, key: str, salida: str) -> Dict:
    import requests
    os.makedirs(salida, exist_ok=True)
    resumen = {'generado': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'tablas': {}}
    for t in tablas(url, key):
        filas = bajar(url, key, t)
        with open(os.path.join(salida, t + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(filas, fh, ensure_ascii=False, separators=(',', ':'), default=str)
        resumen['tablas'][t] = len(filas)
    r = requests.post(url.rstrip('/') + '/rest/v1/rpc/respaldo_auth', headers=_hdr(key, {'Content-Type': 'application/json'}), json={}, timeout=60)
    if not r.ok:
        raise RuntimeError('respaldo_auth: HTTP %s %s' % (r.status_code, r.text[:200]))
    auth = r.json() or {}
    with open(os.path.join(salida, '_auth.json'), 'w', encoding='utf-8') as fh:
        json.dump(auth, fh, ensure_ascii=False, separators=(',', ':'), default=str)
    resumen['cuentas'] = len(auth.get('users') or [])
    with open(os.path.join(salida, 'resumen.json'), 'w', encoding='utf-8') as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=1)
    return resumen


def restaurar(url: str, key: str, carpeta: str) -> Dict:
    """Sube cada tabla con upsert (no borra lo que ya haya). Las cuentas no: van con SQL (ver arriba)."""
    import requests
    hecho = {}
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith('.json') or nombre.startswith('_') or nombre == 'resumen.json':
            continue
        t = nombre[:-5]
        with open(os.path.join(carpeta, nombre), encoding='utf-8') as fh:
            filas = json.load(fh)
        for i in range(0, len(filas), 500):
            r = requests.post(url.rstrip('/') + '/rest/v1/' + t, json=filas[i:i + 500], timeout=120,
                              headers=_hdr(key, {'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates,return=minimal'}))
            if not r.ok:
                raise RuntimeError('%s: HTTP %s %s' % (t, r.status_code, r.text[:200]))
        hecho[t] = len(filas)
    return hecho


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=os.path.join('respaldo', dt.date.today().isoformat()))
    ap.add_argument('--restaurar', default=None)
    a = ap.parse_args()
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        print('faltan SUPABASE_URL / SUPABASE_SERVICE_KEY')
        return 2
    if a.restaurar:
        print(json.dumps(restaurar(url, key, a.restaurar), ensure_ascii=False))
        return 0
    res = respaldar(url, key, a.salida)
    total = sum(res['tablas'].values())
    print('respaldo: %d tablas, %d filas, %d cuentas' % (len(res['tablas']), total, res['cuentas']))
    # un respaldo vacío es un fallo (mejor rojo que un archivo inservible)
    if not res['tablas'] or not res['tablas'].get('picks') or not res['cuentas']:
        print('respaldo incompleto: %s' % json.dumps(res, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
