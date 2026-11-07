#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lo que `requests.get` hace distinto en el servidor. Sin estas variables no hace nada.

`SERVIDOR_PROCESOS`: reusa la conexión. Medido contra ESPN desde el servidor: 0,38 s por petición, y
0,18 son el saludo TLS. Las cookies no se guardan: cada petición viaja como si fuera la primera.

`FOTO_PRECIOS_TTL` y `FOTO_PRECIOS_GRABAR`: la API de la MLB responde 406 al servidor y no se intenta
pasar. Como con Pinnacle y Playdoit (`foto_precios.py`), GitHub graba las respuestas y el servidor las lee.
"""
import http.cookiejar
import json
import os

import requests
from requests.adapters import HTTPAdapter

CONEXIONES = 32
SOLO_EN_LA_FOTO = 'https://statsapi.mlb.com/'


def _de_la_foto(url, params):
    import cuotas_multi as cm

    datos = cm._leer_cache(cm._foto_clave(url, params))
    if datos is None:
        raise requests.ConnectionError('sin foto para %s' % url)
    respuesta = requests.Response()
    respuesta.status_code = 200
    respuesta.url = url
    respuesta.encoding = 'utf-8'
    respuesta._content = json.dumps(datos, ensure_ascii=False).encode('utf-8')
    return respuesta


def _grabar(url, params, respuesta):
    import cuotas_multi as cm

    try:
        cm._escribir_cache(cm._foto_clave(url, params), respuesta.json())
    except ValueError:
        pass


def activar() -> None:
    reusar = int(os.environ.get('SERVIDOR_PROCESOS') or 1) > 1
    leer, grabar = bool(os.environ.get('FOTO_PRECIOS_TTL')), bool(os.environ.get('FOTO_PRECIOS_GRABAR'))
    if not (reusar or leer or grabar) or getattr(requests.api.request, 'reusa', False):
        return
    sesion = requests.Session()
    sesion.cookies.set_policy(http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))
    for esquema in ('https://', 'http://'):
        sesion.mount(esquema, HTTPAdapter(pool_connections=CONEXIONES, pool_maxsize=CONEXIONES))

    def request(method, url, **kwargs):
        de_la_foto = str(url).startswith(SOLO_EN_LA_FOTO)
        if de_la_foto and leer:
            return _de_la_foto(url, kwargs.get('params'))
        respuesta = sesion.request(method=method, url=url, **kwargs)
        if de_la_foto and grabar and respuesta.ok:
            _grabar(url, kwargs.get('params'), respuesta)
        return respuesta

    request.reusa = True
    requests.api.request = request


activar()
