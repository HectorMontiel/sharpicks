#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v568 — «ANTES DEL PARTIDO» DE NHL, NBA, NFL Y MLB, CON LO QUE SE APUESTA EN CADA UNO.

El usuario: «en la NHL no veo lo mismo del análisis previo con el histórico y estadística que en fútbol; no serán córners,
pero sí puntos, etc.: correlaciónalo con lo que hay en el mercado». Cada estadística responde a un mercado que Playdoit ofrece:

  NHL  total y goles por equipo, ambos marcan, primer gol, ¿habrá prórroga?, 1.er periodo; tiros y power play para leerlos.
  NBA  total y puntos por equipo, 1.ª mitad, 1.er cuarto, triples, asistencias, rebotes, robos, bloqueos.
  NFL  total y puntos por equipo, 1.ª mitad, 1.er cuarto, yardas (totales, por pase, por tierra), pérdidas y sacks.
  MLB  total y carreras por equipo, primeras 5 entradas, hits, jonrones y errores.

La fuente es ESPN: calendario del equipo y boxscore de sus últimos partidos. Sólo datos reales: lo que ESPN no trae se queda fuera.
El resultado tiene la misma forma que el contexto del fútbol (fl, fv, sl, sv, ul, uv, h2h, bl, bv). Nunca lanza.
"""
import datetime as dt
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

logger = logging.getLogger('contexto_deportes')
BASE = 'https://site.api.espn.com/apis/site/v2/sports/%s/'
DEPORTES = {'NHL', 'NBA', 'NFL', 'MLB'}
N = 10                     # los últimos 10, como en el fútbol
N_TABLA = 5
PRESUPUESTO_S = 300        # por pasada del exportador: si ESPN va lento, el resto de los partidos se queda sin contexto
HILOS = 8
_MEMO: Dict = {}
_LOCK = threading.Lock()
_INICIO: List[float] = []

ESTADO = {'Out': 'fuera', 'Day-To-Day': 'duda', 'Questionable': 'duda', 'Doubtful': 'duda', 'Injured Reserve': 'lesión larga',
          'Suspension': 'suspendido', 'Suspended': 'suspendido', '10-Day-IL': 'lesionado', '15-Day-IL': 'lesionado', '60-Day-IL': 'lesión larga'}


def _get(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    k = (url, tuple(sorted((params or {}).items())))
    with _LOCK:
        if k in _MEMO:
            return _MEMO[k]
    if _INICIO and time.monotonic() - _INICIO[0] > PRESUPUESTO_S:
        return None
    try:
        import requests
        r = requests.get(url, params=params, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = r.json() if r.ok else None
    except Exception as e:
        logger.debug('[contexto] %s: %s', url, e)
        d = None
    with _LOCK:
        _MEMO[k] = d
    return d


def _num(x) -> Optional[float]:
    try:
        return float(str(x).split('-')[0].split('/')[0])
    except (TypeError, ValueError):
        return None


def _stats(equipo: Dict, dep: str) -> Dict:
    """{estadística: valor} del boxscore de un equipo, con las claves del deporte."""
    if dep == 'MLB':
        grupos = {g.get('name'): {s.get('name'): s.get('displayValue') for s in g.get('stats') or []} for g in equipo.get('statistics') or []}
        bat, fil = grupos.get('batting') or {}, grupos.get('fielding') or {}
        crudo = {'hit': bat.get('hits'), 'hr': bat.get('homeRuns'), 'err': fil.get('errors')}
    else:
        st = {s.get('name'): s.get('displayValue') for s in equipo.get('statistics') or []}
        if dep == 'NHL':
            crudo = {'tir': st.get('shotsTotal'), 'hit': st.get('hits'), 'ppg': st.get('powerPlayGoals'), 'ppo': st.get('powerPlayOpportunities')}
        elif dep == 'NBA':
            crudo = {'t3': st.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted'), 'reb': st.get('totalRebounds'), 'ast': st.get('assists'),
                     'rob': st.get('steals'), 'blq': st.get('blocks'), 'per': st.get('totalTurnovers')}
        else:
            crudo = {'yds': st.get('totalYards'), 'ypa': st.get('netPassingYards'), 'yru': st.get('rushingYards'), 'per': st.get('turnovers'),
                     'sac': st.get('sacksYardsLost'), 'fd': st.get('firstDowns')}
    return {k: _num(v) for k, v in crudo.items() if _num(v) is not None}


def detalle(ruta: str, eid: str, dep: str) -> Dict:
    """Del boxscore: {id de equipo: {'s': estadísticas, 'lin': puntos por periodo}, 'primero': id del que anotó primero}."""
    s = _get(BASE % ruta + 'summary', {'event': eid}) or {}
    out: Dict = {}
    for t in (s.get('boxscore') or {}).get('teams') or []:
        out[str((t.get('team') or {}).get('id'))] = {'s': _stats(t, dep)}
    comp = ((s.get('header') or {}).get('competitions') or [{}])[0]
    for c in comp.get('competitors') or []:
        lin = [_num(x.get('displayValue')) for x in c.get('linescores') or []]
        out.setdefault(str((c.get('team') or {}).get('id')), {'s': {}})['lin'] = [x for x in lin if x is not None]
    jug = [p for p in (s.get('plays') or []) if p.get('scoringPlay')] or (s.get('scoringPlays') or [])
    if jug:
        out['primero'] = str((jug[0].get('team') or {}).get('id'))
    return out


def _partidos_equipo(ruta: str, tid: str, antes: dt.datetime) -> List[Dict]:
    """Los partidos terminados del equipo antes del pitido, del más reciente al más viejo; temporada actual y, si no alcanza, la anterior."""
    url = BASE % ruta + 'teams/%s/schedule' % tid
    d = _get(url) or {}
    evs = list(d.get('events') or [])
    anio = (d.get('season') or {}).get('year')
    if anio:
        evs += (_get(url, {'season': int(anio) - 1}) or {}).get('events') or []
    out, vistos = [], set()
    for e in evs:
        c = (e.get('competitions') or [{}])[0]
        if not ((c.get('status') or {}).get('type') or {}).get('completed') or e.get('id') in vistos:
            continue
        try:
            f = dt.datetime.fromisoformat(str(e.get('date')).replace('Z', '+00:00'))
        except ValueError:
            continue
        if f >= antes:
            continue
        cs = c.get('competitors') or []
        yo = next((x for x in cs if str((x.get('team') or {}).get('id')) == str(tid)), None)
        rv = next((x for x in cs if str((x.get('team') or {}).get('id')) != str(tid)), None)
        if not yo or not rv:
            continue
        marc = lambda x: _num((x.get('score') or {}).get('displayValue') if isinstance(x.get('score'), dict) else x.get('score'))
        gf, gc = marc(yo), marc(rv)
        if gf is None or gc is None:
            continue
        vistos.add(e.get('id'))
        out.append({'id': e.get('id'), 'fecha': f, 'local': yo.get('homeAway') == 'home', 'gf': gf, 'gc': gc, 'rid': str((rv.get('team') or {}).get('id')),
                    'rival': (rv.get('team') or {}).get('shortDisplayName') or (rv.get('team') or {}).get('displayName') or '',
                    'nombre': (yo.get('team') or {}).get('displayName') or '', 'nrival': (rv.get('team') or {}).get('displayName') or ''})
    return sorted(out, key=lambda x: x['fecha'], reverse=True)


def _con_detalle(ruta: str, tid: str, ps: List[Dict], dep: str) -> List[Dict]:
    with ThreadPoolExecutor(HILOS) as ex:
        dets = list(ex.map(lambda x: detalle(ruta, x['id'], dep), ps))
    for x, d in zip(ps, dets):
        yo, rv = d.get(str(tid)) or {}, d.get(x['rid']) or {}
        x.update(s=yo.get('s') or {}, c=rv.get('s') or {}, lf=yo.get('lin') or [], lc=rv.get('lin') or [], primero=d.get('primero'), tid=str(tid))
    return ps


def _media(vals: List[Optional[float]], dec: int = 1) -> Optional[float]:
    v = [x for x in vals if x is not None]
    return round(sum(v) / len(v), dec) if v else None


def _pct(vals: List[Optional[bool]]) -> Optional[float]:
    v = [x for x in vals if x is not None]
    return round(sum(1 for x in v if x) / len(v), 2) if v else None


def _periodos(x: Dict, n: int) -> Optional[float]:
    """Lo de los dos equipos en los primeros n periodos."""
    if len(x['lf']) < n or len(x['lc']) < n:
        return None
    return sum(x['lf'][:n]) + sum(x['lc'][:n])


def _reg(dep: str) -> int:
    return {'NHL': 3, 'NBA': 4, 'NFL': 4, 'MLB': 9}[dep]


def promedios(ps: List[Dict], dep: str) -> Dict:
    """Los promedios del deporte: cada clave corresponde a un mercado de Playdoit o ayuda a leerlo."""
    tot = [x['gf'] + x['gc'] for x in ps]
    out = {'n': len(ps), 'gf': _media([x['gf'] for x in ps]), 'gc': _media([x['gc'] for x in ps]), 'tot': _media(tot),
           'pro': _pct([len(x['lf']) > _reg(dep) if x['lf'] else None for x in ps])}
    st = lambda k, fuente='s': _media([x[fuente].get(k) for x in ps])
    if dep == 'NHL':
        ppg, ppo = sum(x['s'].get('ppg') or 0 for x in ps), sum(x['s'].get('ppo') or 0 for x in ps)
        out.update(o55=_pct([t > 5.5 for t in tot]), ambos=_pct([x['gf'] > 0 and x['gc'] > 0 for x in ps]), p1=_media([_periodos(x, 1) for x in ps]),
                   pa=_pct([(x['primero'] == x['tid']) if x.get('primero') else None for x in ps]), tir=st('tir'), tirc=st('tir', 'c'),
                   pp=round(ppg / ppo, 2) if ppo else None, hit=st('hit'))
    elif dep == 'NBA':
        out.update(h1=_media([_periodos(x, 2) for x in ps]), q1=_media([_periodos(x, 1) for x in ps]), t3=st('t3'), t3c=st('t3', 'c'), ast=st('ast'),
                   reb=st('reb'), rob=st('rob'), blq=st('blq'), per=st('per'))
    elif dep == 'NFL':
        out.update(h1=_media([_periodos(x, 2) for x in ps]), q1=_media([_periodos(x, 1) for x in ps]), yds=st('yds'), ydc=st('yds', 'c'), ypa=st('ypa'),
                   yru=st('yru'), per=st('per'), sac=st('sac'), fd=st('fd'))
    else:
        out.update(f5=_media([_periodos(x, 5) for x in ps]), hit=st('hit'), hr=st('hr'), err=st('err'))
    return {k: v for k, v in out.items() if v is not None}


def _par(x: Dict, k: str) -> Optional[List]:
    a, b = x['s'].get(k), x['c'].get(k)
    return None if a is None or b is None else [int(a), int(b)]


def _parp(x: Dict, n: int) -> Optional[List]:
    if len(x['lf']) < n or len(x['lc']) < n:
        return None
    return [int(sum(x['lf'][:n])), int(sum(x['lc'][:n]))]


def ultimos(ps: List[Dict], dep: str) -> List:
    """Del más reciente al más viejo: [fecha, rival, local, a favor, en contra, y tres pares a favor-en contra del deporte]."""
    out = []
    for x in ps[:N_TABLA]:
        if dep == 'NHL':
            extra = [_par(x, 'tir'), _parp(x, 1), _par(x, 'ppg')]
        elif dep == 'NBA':
            extra = [_parp(x, 1), _par(x, 't3'), _par(x, 'reb')]
        elif dep == 'NFL':
            extra = [_parp(x, 2), _par(x, 'yds'), _par(x, 'per')]
        else:
            extra = [_par(x, 'hit'), _par(x, 'err'), _parp(x, 5)]
        out.append([x['fecha'].strftime('%d/%m'), x['rival'], 1 if x['local'] else 0, int(x['gf']), int(x['gc'])] + extra)
    return out


def _forma(ps: List[Dict]) -> str:
    return ''.join('G' if x['gf'] > x['gc'] else 'P' if x['gf'] < x['gc'] else 'E' for x in ps[:N_TABLA][::-1])


def _bajas(s: Dict, tid: str) -> List[str]:
    for t in s.get('injuries') or []:
        if str((t.get('team') or {}).get('id')) == str(tid):
            out = []
            for i in t.get('injuries') or []:
                n = (i.get('athlete') or {}).get('displayName')
                if n:
                    est = i.get('status') or ''
                    out.append('%s (%s)' % (n, ESTADO.get(est, est.lower())) if est else n)
            return out[:6]
    return []


def contexto(p: Dict, ahora: Optional[dt.datetime] = None) -> Optional[Dict]:
    """El contexto del partido o None: sin partido de ESPN, ya jugado, o si no se sabe quién es quién."""
    try:
        dep, espn = p.get('deporte'), str(p.get('espn') or '')
        if dep not in DEPORTES or ':' not in espn or ' vs ' not in str(p.get('partido') or ''):
            return None
        if not _INICIO:
            _INICIO.append(time.monotonic())
        ahora = ahora or dt.datetime.now(dt.timezone.utc)
        ruta, eid = espn.split(':', 1)
        s = _get(BASE % ruta + 'summary', {'event': eid}) or {}
        comp = ((s.get('header') or {}).get('competitions') or [{}])[0]
        cs = comp.get('competitors') or []
        if len(cs) < 2:
            return None
        try:
            ini = dt.datetime.fromisoformat(str(comp.get('date') or p.get('inicio')).replace('Z', '+00:00').replace(' ', 'T'))
            ini = ini if ini.tzinfo else ini.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            ini = ahora
        if ahora - ini > dt.timedelta(hours=8):       # ya se jugó: no se gasta en lo que ya no se va a apostar
            return None
        import liquidar_pendientes as lq
        L, _, V = str(p['partido']).partition(' vs ')
        nombre = lambda c: (c.get('team') or {}).get('displayName') or ''
        c0, c1 = cs[0], cs[1]
        directo = lq._parecido(nombre(c0), L) + lq._parecido(nombre(c1), V)
        vuelta = lq._parecido(nombre(c0), V) + lq._parecido(nombre(c1), L)
        if max(directo, vuelta) < 1.0:
            return None
        cl, cv = (c0, c1) if directo >= vuelta else (c1, c0)
        tl, tv = str(cl['team']['id']), str(cv['team']['id'])
        al, av = _partidos_equipo(ruta, tl, ini), _partidos_equipo(ruta, tv, ini)
        if not al or not av:
            return None
        pl, pv = _con_detalle(ruta, tl, al[:N], dep), _con_detalle(ruta, tv, av[:N], dep)
        ctx = {'fl': _forma(pl), 'fv': _forma(pv), 'sl': promedios(pl, dep), 'sv': promedios(pv, dep), 'ul': ultimos(pl, dep), 'uv': ultimos(pv, dep),
               'h2h': [[x['fecha'].strftime('%d/%m/%y'), x['nombre'] if x['local'] else x['nrival'],
                        '%d-%d' % ((x['gf'], x['gc']) if x['local'] else (x['gc'], x['gf'])), x['nrival'] if x['local'] else x['nombre']]
                       for x in al if x['rid'] == tv][:5]}
        bl, bv = _bajas(s, tl), _bajas(s, tv)
        if bl:
            ctx['bl'] = bl
        if bv:
            ctx['bv'] = bv
        return {k: v for k, v in ctx.items() if v} or None
    except Exception as e:
        logger.debug('[contexto] %s: %s', p.get('partido'), e)
        return None
