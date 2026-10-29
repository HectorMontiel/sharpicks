#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v513 — EL HISTORIAL PÚBLICO DEL PULSO: qué dijo en el 60' y el 70', y qué salió.

Para cada partido de fútbol de hoy y ayer ya terminado (con su partido de ESPN): con el comentario minuto a
minuto de ESPN se arma el marcador y los córners del 60' y del 70', se calcula el Pulso con el MISMO modelo y
la MISMA cuenta que la página (`web/pulso.js`, `web/pulso_modelo.json`) y se apunta en `pulso_historial` con
el resultado al pitido. Una fila por partido, minuto y mercado; nadie la retoca después (si ya está, no se
pisa). Nunca lanza: si algo falla, esa pasada no apunta."""
import bisect
import datetime as dt
import json
import logging
import math
import os
import re
from typing import Dict, List, Optional

logger = logging.getLogger('pulso_historial')
AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(AQUI, 'web', 'pulso_modelo.json')
TOPE = {'gol': 0.85, 'gol2': 0.5, 'gol_l': 0.75, 'gol_v': 0.65}
MINUTOS = (60, 70)
HASTA = {'gol': 80, 'gol2': 80, 'gol_l': 80, 'gol_v': 80, 'cor1': 85, 'cor2': 85, 'cor3': 85}   # lo medido


def _interp(x: float, xs: List[float], ys: List[float]) -> float:
    if not xs:
        return x
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_left(xs, x)
    t = (x - xs[i - 1]) / ((xs[i] - xs[i - 1]) or 1)
    return ys[i - 1] + t * (ys[i] - ys[i - 1])


def prob(M: Dict, k: str, f: Dict) -> Optional[float]:
    m = M['modelos'].get(k)
    if not m or f.get('t', 0) > HASTA.get(k, 90):
        return None
    z = m['inter']
    for c, b in zip(m['cols'], m['coef']):
        if f.get(c) is None:
            return None
        z += b * f[c]
    return min(_interp(1 / (1 + math.exp(-z)), m['iso_x'], m['iso_y']), TOPE.get(k, 0.97))


def rasgos(M: Dict, ctx: Dict, t: float, gh: int, ga: int, c: Optional[int]) -> Dict:
    """La misma cuenta que `rasgos` de web/pulso.js."""
    G, K = M['G'], M['K']
    enc = lambda m, n: ((float(m or G)) * float(n or 0) + G * K) / (float(n or 0) + K)
    rem = 94 - t
    f = {'t': t, 'tot': gh + ga, 'dif': abs(gh - ga), 'emp': int(gh == ga), 'sig': gh - ga}
    sl, sv = (ctx or {}).get('sl'), (ctx or {}).get('sv')
    if sl and sv:
        lh = (enc(sl.get('gf'), sl.get('n')) + enc(sv.get('gc'), sv.get('n'))) / 2 * rem / 94
        la = (enc(sv.get('gf'), sv.get('n')) + enc(sl.get('gc'), sl.get('n'))) / 2 * rem / 94
        f.update(lh=math.log(max(lh, 0.03)), la=math.log(max(la, 0.03)), ltot=math.log(max(lh + la, 0.05)))
    if c is not None:
        f.update(c=c, ritmo=c / t * rem)
    return f


def _minuto(v: str) -> Optional[float]:
    m = re.findall(r'\d+', v or '')
    return (int(m[0]) + (int(m[1]) / 100.0 if len(m) > 1 else 0)) if m else None


def estado_espn(d: Dict, girado: bool) -> Optional[Dict]:
    """Goles y córners por minuto del comentario de ESPN, en el orden de NUESTRO «A vs B»."""
    comp = ((d.get('header') or {}).get('competitions') or [{}])[0]
    if not (((comp.get('status') or {}).get('type') or {}).get('completed')):
        return None
    cs = comp.get('competitors') or []
    h = next((c for c in cs if c.get('homeAway') == 'home'), {})
    a = next((c for c in cs if c.get('homeAway') == 'away'), {})
    goles, cor = [], []
    for c in d.get('commentary') or []:
        t = _minuto((c.get('time') or {}).get('displayValue')); x = c.get('text') or ''
        if t is None:
            continue
        m = re.match(r'(?:Goal!|Own Goal by [^.]+\.)\s+(.+?) (\d+), (.+?) (\d+)\.', x)
        if m:
            goles.append((t, int(m.group(2)), int(m.group(4))))
        elif x.startswith('Corner,'):
            cor.append(t)
    fin = (int(h.get('score') or 0), int(a.get('score') or 0))
    if goles and (goles[-1][1], goles[-1][2]) != fin:
        return None                                    # el comentario no cuadra con el marcador: no se apunta
    if girado:
        goles = [(t, y, x) for t, x, y in goles]; fin = (fin[1], fin[0])
    return {'goles': goles, 'cor': cor, 'fin': fin}


def lecturas(M: Dict, p: Dict, e: Dict) -> List[Dict]:
    out = []
    L, _, V = p['partido'].partition(' vs ')
    cfin = len(e['cor']) if e['cor'] else None
    for t in MINUTOS:
        g = [x for x in e['goles'] if x[0] <= t]
        gh, ga = (g[-1][1], g[-1][2]) if g else (0, 0)
        c = sum(1 for x in e['cor'] if x <= t) if e['cor'] else None
        f = rasgos(M, p.get('ctx') or {}, float(t), gh, ga, c)
        fh, fa = e['fin']
        res = {'gol': fh + fa > gh + ga, 'gol2': fh + fa - gh - ga >= 2, 'gol_l': fh > gh, 'gol_v': fa > ga}
        if c is not None:
            res.update(cor1=cfin - c >= 1, cor2=cfin - c >= 2, cor3=cfin - c >= 3)
        for k, ok in res.items():
            pr = prob(M, k, f)
            if pr is None:
                continue
            out.append({'partido': p['partido'], 'fecha': p['fecha'], 'liga': p.get('liga'), 'minuto': t, 'mercado': k,
                        'marcador': '%d-%d' % (gh, ga), 'prob': round(pr, 3), 'acierto': bool(ok)})
    return out


def apuntar(filas_web: List[Dict], url: str = None, key: str = None, sesion=None) -> int:
    url = url or os.environ.get('SUPABASE_URL', ''); key = key or os.environ.get('SUPABASE_SERVICE_KEY', '')
    if not url or not key:
        return 0
    try:
        import requests
        sesion = sesion or requests.Session()
        with open(MODELO, encoding='utf-8') as fh:
            M = json.load(fh)
        vistos, filas = set(), []
        for p in filas_web:
            if p.get('deporte') != 'Fútbol' or not p.get('espn') or ':' not in str(p['espn']):
                continue
            k = (p['partido'], p.get('fecha'))
            if k in vistos or not p.get('fecha'):
                continue
            vistos.add(k)
            ruta, ev = str(p['espn']).split(':', 1)
            try:
                d = sesion.get('https://site.api.espn.com/apis/site/v2/sports/%s/summary' % ruta, params={'event': ev}, timeout=20).json()
            except Exception:
                continue
            e = estado_espn(d, bool(p.get('girado')))
            if e:
                filas += lecturas(M, p, e)
        if not filas:
            return 0
        r = sesion.post(url.rstrip('/') + '/rest/v1/pulso_historial', timeout=60, json=filas,
                        headers={'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                                 'Prefer': 'resolution=ignore-duplicates,return=minimal'})
        if r.status_code >= 300:
            logger.warning('[pulso] no se apuntó: %s %s', r.status_code, r.text[:200])
            return 0
        return len(filas)
    except Exception as ex:
        logger.warning('[pulso] sin historial: %s', ex)
        return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    hoy = json.load(open(os.path.join(AQUI, 'web', 'datos', 'hoy.json'), encoding='utf-8'))
    filas = [p for p in hoy.get('picks', []) + hoy.get('analisis', []) if p.get('estado') in ('verde', 'roja', 'nula', 'vivo')]
    print('pulso: %d lecturas apuntadas' % apuntar(filas))
