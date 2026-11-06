#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v584 — LOS PICKS DE PAGO NO SE PUBLICAN EN CLARO EN EL REPOSITORIO.

El repositorio es público y los flujos guardan en git lo que calcula el precálculo. Medido el 6-nov-2026: de 400 picks
premium por jugar, 400 se leían gratis en `anunciadas_dia.json` y 374 en `pronostico_dia.json`, mientras el sitio y la
base los enseñaban tapados.

Estos archivos se guardan comprimidos y cifrados en `cajon/` (AES-256, clave en el secreto DATOS_CLAVE; misma receta que
`respaldo_base.yml`). Cada flujo los abre al empezar; en claro sólo existen en el disco del runner o del PC, y `.gitignore`
impide volver a subirlos.

    python cajon.py abrir [--estricto]    cajon/ → archivos en claro (--estricto: sin clave o sin cajón, falla)
    python cajon.py cerrar                archivos en claro → cajon/ (sólo los que cambiaron)

Sin el secreto (el PC, por ejemplo) la clave se lee de ARCHIVO_CLAVE_LOCAL, fuera del repositorio.
"""
from __future__ import annotations

import gzip
import os
import subprocess
import sys
from typing import Optional

ARCHIVOS = ('pronostico_dia.json', 'anunciadas_dia.json', 'arriesgadas_seguimiento.csv')
CAJON = 'cajon'
ARCHIVO_CLAVE_LOCAL = 'D:/Claude/DATOS_CLAVE_sharpicks.txt'


def clave() -> Optional[str]:
    k = (os.environ.get('DATOS_CLAVE') or '').strip()
    if k:
        return k
    try:
        with open(ARCHIVO_CLAVE_LOCAL, encoding='utf-8') as f:
            return f.read().strip() or None
    except OSError:
        return None


def _openssl(datos: bytes, k: str, descifrar: bool) -> bytes:
    orden = ['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', '100000', '-pass', 'env:DATOS_CLAVE']
    orden += ['-d'] if descifrar else ['-salt']
    r = subprocess.run(orden, input=datos, capture_output=True, env=dict(os.environ, DATOS_CLAVE=k))
    if r.returncode:
        raise ValueError('openssl no pudo %s' % ('descifrar' if descifrar else 'cifrar'))
    return r.stdout


def cifrar(claro: bytes, k: str) -> bytes:
    return _openssl(gzip.compress(claro, 9, mtime=0), k, False)


def descifrar(cifrado: bytes, k: str) -> bytes:
    return gzip.decompress(_openssl(cifrado, k, True))


def ruta_cajon(nombre: str, raiz: str = '.') -> str:
    return os.path.join(raiz, CAJON, nombre + '.gz.enc')


def _escribir(ruta: str, datos: bytes) -> None:
    os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
    tmp = ruta + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(datos)
    os.replace(tmp, ruta)


def cerrar(raiz: str = '.', k: Optional[str] = None) -> int:
    """Cifra lo que cambió: la sal hace distinto cada cifrado, y sin esta comparación habría un commit en cada pasada."""
    k = k or clave()
    if not k:
        print('::error::cajón: falta DATOS_CLAVE; no se cifra nada')
        return 1
    for nombre in ARCHIVOS:
        origen, destino = os.path.join(raiz, nombre), ruta_cajon(nombre, raiz)
        if not os.path.exists(origen):
            continue
        with open(origen, 'rb') as f:
            claro = f.read()
        if os.path.exists(destino):
            try:
                with open(destino, 'rb') as f:
                    if descifrar(f.read(), k) == claro:
                        continue
            except (ValueError, OSError, EOFError):
                pass                    # dañado o con otra clave: se reescribe
        _escribir(destino, cifrar(claro, k))
        print('cajón: %s cifrado' % nombre)
    return 0


def abrir(raiz: str = '.', estricto: bool = False, k: Optional[str] = None) -> int:
    k = k or clave()
    if not k:
        print('%s cajón: falta DATOS_CLAVE; los datos del día no se abren' % ('::error::' if estricto else '::warning::'))
        return 1 if estricto else 0
    malos = 0
    for nombre in ARCHIVOS:
        origen = ruta_cajon(nombre, raiz)
        try:
            with open(origen, 'rb') as f:
                _escribir(os.path.join(raiz, nombre), descifrar(f.read(), k))
        except (ValueError, OSError, EOFError) as e:
            malos += 1
            print('%s cajón: no se abrió %s (%s)' % ('::error::' if estricto else '::warning::', nombre, type(e).__name__))
    return 1 if estricto and malos else 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['abrir']:
        raise SystemExit(abrir(estricto='--estricto' in args))
    if args[:1] == ['cerrar']:
        raise SystemExit(cerrar())
    print(__doc__)
    raise SystemExit(2)
