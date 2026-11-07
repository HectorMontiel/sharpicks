#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v594 — La foto de precios: lo único que no corre en el servidor propio.

Desde la IP del servidor, Cloudflare responde 403 a Pinnacle y a Playdoit. No se
intenta pasar: ni proxies, ni simular un navegador, ni otra librería. Una tarea de
GitHub, donde esas lecturas ya corren hoy, baja los precios y los deja en un
paquete; el servidor lo descarga y `cuotas_multi` lo lee (ver `FOTO_TTL`).

    python foto_precios.py --generar     (GitHub) baja y empaqueta
    python foto_precios.py --bajar       (servidor) descarga y desempaca
    python foto_precios.py --estado      qué tan vieja está la foto
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import sys
import tarfile
import time

PAQUETE = 'foto_precios.tar.gz'
ETIQUETA = os.environ.get('RELEASE_FOTO', 'foto-precios')
META = 'foto_meta.json'
HILOS = 6


def generar(salida: str = PAQUETE) -> int:
    """Baja todo en limpio. Devuelve 0 si hay precios de las dos fuentes."""
    os.environ['FOTO_PRECIOS_GRABAR'] = '1'
    os.environ.pop('FOTO_PRECIOS_TTL', None)
    import beisbol_pitchers
    import cuotas_multi as cm

    cm.FOTO_GRABAR, cm.FOTO_TTL = True, 0
    for patron in ('pinnacle_*', 'playdoit_*', 'foto_raw_*'):
        for f in glob.glob(os.path.join(cm.CACHE_DIR, patron)):
            os.remove(f)
    ini = time.time()
    cuentas = {'pinnacle': {}, 'playdoit': {}, 'tablero': {}}
    for dep in cm.DEPORTES:
        cuentas['pinnacle'][dep] = len(cm._indice_pinnacle(dep))
        cm.totales_del_deporte(dep)
    try:
        beisbol_pitchers.props_ponches()
    except Exception as e:
        print('aviso: ponches sin grabar: %s' % type(e).__name__)
    for dep in cm.ALTENAR_SPORT:
        idx = cm._indice_playdoit(dep)
        cuentas['playdoit'][dep] = len(idx)

        def _uno(v, _d=dep):
            try:
                return bool(cm.mercados_playdoit(_d, v['home'], v['away']))
            except Exception:
                return False

        with cf.ThreadPoolExecutor(HILOS) as ex:
            cuentas['tablero'][dep] = sum(ex.map(_uno, list(idx.values())))
    doc = {'generado': time.time(), 'segundos': round(time.time() - ini), **cuentas}
    with open(os.path.join(cm.CACHE_DIR, META), 'w', encoding='utf-8') as f:
        json.dump(doc, f)
    with tarfile.open(salida, 'w:gz') as tar:
        for patron in ('pinnacle_*', 'playdoit_*', 'foto_raw_*', META):
            for f in glob.glob(os.path.join(cm.CACHE_DIR, patron)):
                tar.add(f, arcname=os.path.basename(f))
    print(json.dumps(doc, ensure_ascii=False))
    print('paquete: %.1f MB' % (os.path.getsize(salida) / 1e6))
    return 0 if cuentas['pinnacle'].get('futbol') and cuentas['playdoit'].get('futbol') else 1


def desempacar(paquete: str = PAQUETE, destino: str = None) -> int:
    """Sólo archivos sueltos con los nombres esperados: nada fuera de la carpeta."""
    import cuotas_multi as cm

    destino = destino or cm.CACHE_DIR
    os.makedirs(destino, exist_ok=True)
    n = 0
    with tarfile.open(paquete, 'r:gz') as tar:
        for m in tar.getmembers():
            nombre = m.name
            valido = (nombre == META or nombre.startswith(('pinnacle_', 'playdoit_', 'foto_raw_')))
            if not m.isfile() or '/' in nombre or '\\' in nombre or not valido:
                continue
            with tar.extractfile(m) as origen, open(os.path.join(destino, nombre), 'wb') as dest:
                dest.write(origen.read())
            os.utime(os.path.join(destino, nombre), (m.mtime, m.mtime))    # la edad real
            n += 1
    return n


def bajar(paquete: str = PAQUETE) -> int:
    """Descarga el último paquete. Si falla, se queda la foto anterior."""
    import requests
    import modelos_remotos as mr

    h = {'Accept': 'application/octet-stream', 'User-Agent': 'sharpicks'}
    tok = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN') or ''
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    rel = requests.get('https://api.github.com/repos/%s/releases/tags/%s' % (mr.REPO, ETIQUETA),
                       headers={k: v for k, v in h.items() if k != 'Accept'}, timeout=30)
    if rel.status_code != 200:
        print('sin foto: release %s' % rel.status_code)
        return 1
    url = next((a['url'] for a in rel.json().get('assets') or [] if a['name'] == PAQUETE), None)
    if not url:
        print('sin foto: el release no trae el paquete')
        return 1
    temporal = '%s.%d.tmp' % (paquete, os.getpid())  # dos flujos pueden bajarla a la vez
    with requests.get(url, headers=h, stream=True, timeout=120) as r:
        if r.status_code != 200:
            print('sin foto: descarga %s' % r.status_code)
            return 1
        with open(temporal, 'wb') as f:
            for trozo in r.iter_content(1 << 20):
                f.write(trozo)
    n = desempacar(temporal)
    os.remove(temporal)
    print('foto: %d archivos' % n)
    return 0 if n else 1


def estado() -> dict:
    import cuotas_multi as cm

    try:
        with open(os.path.join(cm.CACHE_DIR, META), encoding='utf-8') as f:
            doc = json.load(f)
    except Exception:
        return {'hay': False}
    doc['hay'] = True
    doc['edad_min'] = round((time.time() - doc.get('generado', 0)) / 60, 1)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--generar', action='store_true')
    ap.add_argument('--bajar', action='store_true')
    ap.add_argument('--estado', action='store_true')
    a = ap.parse_args()
    if a.generar:
        return generar()
    if a.bajar:
        return bajar()
    print(json.dumps(estado(), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
