# -*- coding: utf-8 -*-
"""
v492 — LA TABLA DE CLASIFICACIÓN DE CADA LIGA, PARA LA PÁGINA.

El usuario: «hace falta una pestaña para saber en qué lugar van de su clasificación; se debe ver
toda la tabla pero resaltados esos equipos». La de ESPN (`site.api.espn.com/apis/v2/…/standings`,
la misma fuente de los partidos), una vez por liga en cada pasada del exportador, sólo de las ligas
que hoy tienen partido en la página. Las copas no tienen tabla (no se piden). Se escribe en
`web/datos/tablas.json` (público: no es nada del VIP):

    {'generado': …, 'ligas': {'MLS': {'grupos': [{'nombre': 'Eastern Conference',
        'filas': [[pos, equipo, pj, g, e, p, dg, pts, zona], …]}]}}}

`zona` es la nota de ESPN (Champions, descenso…) para pintar la franja de color, o ''.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger('tablas_web')
SALIDA = os.path.join('web', 'datos', 'tablas.json')
URL = 'https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings'


def _num(stats: Dict, k: str):
    v = stats.get(k)
    try:
        return int(float(str(v).replace('+', '')))
    except (TypeError, ValueError):
        return None


def leer(d: Dict) -> List[Dict]:
    """Los grupos de una respuesta de ESPN (una liga normal trae uno; la MLS, dos conferencias)."""
    grupos = []
    for c in (d.get('children') or [d]):
        filas = []
        for e in ((c.get('standings') or {}).get('entries') or []):
            st = {s.get('name'): s.get('value', s.get('displayValue')) for s in e.get('stats') or []}
            nombre = ((e.get('team') or {}).get('displayName')) or ''
            pos = _num(st, 'rank')
            if not nombre or pos is None:
                continue
            filas.append([pos, nombre, _num(st, 'gamesPlayed'), _num(st, 'wins'), _num(st, 'ties'), _num(st, 'losses'),
                          _num(st, 'pointDifferential'), _num(st, 'points'), str(((e.get('note') or {}).get('description')) or '')])
        if filas:
            grupos.append({'nombre': str(c.get('name') or ''), 'filas': sorted(filas, key=lambda x: x[0])})
    return grupos


def generar(filas: List[Dict], claves: Dict[str, str], pedir=None) -> Dict[str, Dict]:
    """Por cada liga de fútbol con partido en la página y código de ESPN, su tabla. Nunca lanza."""
    try:
        import fixtures_espn as fe
        import config_ligas_espn as cfg
        solo = {k for k, v in (getattr(cfg, 'LIGAS', {}) or {}).items() if isinstance(v, dict) and v.get('solo_analisis')}
    except Exception as e:
        logger.warning('[tablas] sin códigos de ESPN: %s', e)
        return {}
    if pedir is None:
        import requests

        def pedir(u):
            r = requests.get(u, timeout=20)
            return r.json() if r.ok else None
    ligas: Dict[str, str] = {}
    for f in filas:
        if f.get('deporte') != 'Fútbol' or not f.get('liga'):
            continue
        clave = claves.get(f.get('partido'))
        code = fe.ESPN_CODIGOS.get(clave or '')
        if code and clave not in solo:
            ligas.setdefault(f['liga'], code)
    out, memo = {}, {}
    for liga, code in ligas.items():
        if code not in memo:
            try:
                memo[code] = leer(pedir(URL.format(code=code)) or {})
            except Exception as e:
                logger.debug('[tablas] %s: %s', code, e)
                memo[code] = []
        if memo[code]:
            out[liga] = {'grupos': memo[code]}
    return out


def escribir(tablas: Dict[str, Dict], ruta: str = SALIDA) -> int:
    # en el servidor `web/datos` aún no existe cuando se escribe esto (hoy.json va después)
    os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump({'generado': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'ligas': tablas},
                  fh, ensure_ascii=False, separators=(',', ':'))
    return len(tablas)
