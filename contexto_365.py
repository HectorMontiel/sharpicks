#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v571 — «ANTES DEL PARTIDO» DE TENIS Y DEL BÉISBOL DE INVIERNO, DESDE 365SCORES.

El usuario: «en tenis no me estás dando absolutamente nada de datos previos» y «en estos partidos de béisbol no tienes nada».
ESPN no cubre al tenis de ITF/Challenger ni a la LVBP, LMP o LIDOM; 365Scores sí, con su historial real:
  Tenis    sets y juegos por set, aces, dobles faltas, quiebres y puntos ganados.
  Béisbol  carreras por entrada (hits y errores, sólo si la liga los trae).
Cada estadística responde a lo que Playdoit ofrece: en tenis hándicap de sets, juegos y 1.er set; en invierno ganador, hándicap y total.
Misma forma que el contexto de los demás deportes (fl, fv, sl, sv, ul, uv, h2h). Nunca lanza.

Son cientos de tenistas: cada pasada tiene su presupuesto y lo ya calculado hace menos de 6 h se reutiliza de lo publicado.

365Scores sólo tiene 47 de 201 partidos de tenis (medido 5-nov-2026): no cubre el ITF. Si no está o se acabó el presupuesto, el tenis sale del
feed diario de Flashscore: 8 días de todo el tenis con sus sets y juegos, sin aces. Una fuente por partido, nunca mezcladas (v436).
"""
import datetime as dt
import logging
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import contexto_deportes as cd

logger = logging.getLogger('contexto_365')
API = 'https://webws.365scores.com/web/'
PARAMS = {'appTypeId': 5, 'langId': 29, 'timezoneName': 'UTC', 'userCountryId': 31}
DEPORTES = {'Béisbol': 7, 'Tenis': 3}
N = {'Béisbol': 10, 'Tenis': 6}       # el tenista juega mucho y cada partido son dos consultas
TOLERANCIA_H = {'Béisbol': 6, 'Tenis': 18}      # el orden de juego del tenis mueve mucho la hora
VIGENCIA_H = 6
PRESUPUESTO_S = 90
HILOS = 12
FS_DIA = 'https://global.flashscore.ninja/2/x/feed/f_2_%d_3_es-mx_1'
FS_DIAS = 8
_FS: List[Dict] = []
SITIO = 'https://sharpicksapp.com/datos/'
_MEMO: Dict = {}
_LOCK = threading.Lock()
_INICIO: List[float] = []
_ST_ACE, _ST_DF, _ST_QB, _ST_PTS = 1, 2, 4, 20
_SOBRA = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'bbc'}


def _get(ruta: str, **q) -> Optional[Dict]:
    k = (ruta, tuple(sorted(q.items())))
    with _LOCK:
        if k in _MEMO:
            return _MEMO[k]
    if _INICIO and time.monotonic() - _INICIO[0] > PRESUPUESTO_S:
        return None
    try:
        import requests
        r = requests.get(API + ruta, params=dict(PARAMS, **q), timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = r.json() if r.ok else None
    except Exception as e:
        logger.debug('[365] %s: %s', ruta, e)
        d = None
    with _LOCK:
        _MEMO[k] = d
    return d


def _fecha(x) -> Optional[dt.datetime]:
    try:
        f = dt.datetime.fromisoformat(str(x).replace('Z', '+00:00').replace(' ', 'T'))
        return f if f.tzinfo else f.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _palabras(x: str) -> set:
    t = unicodedata.normalize('NFD', str(x or '').lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return {w for w in re.findall(r'[a-z0-9]+', t) if w not in _SOBRA}


def mismo_equipo(a: str, b: str) -> bool:
    """«Aragua» = «Tigres de Aragua»: todas las palabras del nombre corto están en el largo. Sólo se usa con los dos equipos y la hora."""
    x, y = _palabras(a), _palabras(b)
    return bool(x and y) and (x <= y or y <= x)


def _coincide(dep: str, a: str, b: str) -> bool:
    if dep == 'Tenis':
        import escudos
        return bool(escudos._jugador(a, b))
    return mismo_equipo(a, b)


def partido365(p: Dict) -> Optional[Dict]:
    """El partido en 365Scores con {g, local, visita}, respetando quién es local en NUESTRO nombre."""
    dep = p.get('deporte')
    L, _, V = str(p.get('partido') or '').partition(' vs ')
    ini = _fecha(p.get('inicio'))
    if not L or not V or ini is None:
        return None
    for d in (ini.date(), ini.date() - dt.timedelta(days=1), ini.date() + dt.timedelta(days=1)):
        c = d.strftime('%d/%m/%Y')
        for g in (_get('games/allscores/', sports=DEPORTES[dep], startDate=c, endDate=c) or {}).get('games') or []:
            f = _fecha(g.get('startTime'))
            if f is None or abs((f - ini).total_seconds()) > TOLERANCIA_H[dep] * 3600:
                continue
            h, a = g.get('homeCompetitor') or {}, g.get('awayCompetitor') or {}
            if _coincide(dep, L, h.get('name')) and _coincide(dep, V, a.get('name')):
                return {'g': g, 'local': h, 'visita': a}
            if _coincide(dep, L, a.get('name')) and _coincide(dep, V, h.get('name')):
                return {'g': g, 'local': a, 'visita': h}
    return None


def _num(x) -> Optional[float]:
    m = re.match(r'\s*(-?\d+(?:\.\d+)?)', str(x))
    return float(m.group(1)) if m else None


def _pct_de(x) -> Optional[float]:
    m = re.search(r'\((\d+)%\)', str(x))
    return float(m.group(1)) / 100 if m else None


def historial(tid, antes: dt.datetime) -> List[Dict]:
    """Sus partidos terminados antes del pitido, del más reciente al más viejo."""
    out = []
    for x in (_get('games/results/', competitors=tid, showOdds='false') or {}).get('games') or []:
        f, h, a = _fecha(x.get('startTime')), x.get('homeCompetitor') or {}, x.get('awayCompetitor') or {}
        if f is None or f >= antes or x.get('statusGroup') != 4:
            continue
        local = str(h.get('id')) == str(tid)
        yo, rv = (h, a) if local else (a, h)
        gf, gc = yo.get('score'), rv.get('score')
        if gf is None or gc is None or gf < 0 or gc < 0 or gf + gc == 0:      # sin marcador o abandono antes de empezar
            continue
        out.append({'id': x.get('id'), 'fecha': f, 'local': local, 'gf': float(gf), 'gc': float(gc), 'tid': str(tid), 'rid': str(rv.get('id')),
                    'rival': rv.get('name') or '', 'nombre': yo.get('name') or '', 'nrival': rv.get('name') or ''})
    return sorted(out, key=lambda z: z['fecha'], reverse=True)


def _detalle(x: Dict, dep: str) -> None:
    """Le pone lo de cada periodo (entradas o sets) y, en tenis, lo del saque y la devolución."""
    g = (_get('game/', gameId=x['id']) or {}).get('game') or {}
    lf, lc, s, c = [], [], {}, {}
    for st in g.get('stages') or []:
        n, a, b = str(st.get('shortName')), st.get('homeCompetitorScore'), st.get('awayCompetitorScore')
        yo, rv = (a, b) if x['local'] else (b, a)
        if yo is None or rv is None or yo < 0 or rv < 0:
            continue
        if re.fullmatch(r'S?\d+', n):
            lf.append(float(yo)); lc.append(float(rv))
        elif n == 'H':
            s['hit'], c['hit'] = float(yo), float(rv)
        elif n == 'E':
            s['err'], c['err'] = float(yo), float(rv)
    if dep == 'Tenis':
        for e in (_get('game/stats/', games=x['id']) or {}).get('statistics') or []:
            quien = s if str(e.get('competitorId')) == x['tid'] else c if str(e.get('competitorId')) == x['rid'] else None
            if quien is None:
                continue
            i, v = e.get('id'), e.get('value')
            if i == _ST_ACE:
                quien['ace'] = _num(v)
            elif i == _ST_DF:
                quien['df'] = _num(v)
            elif i == _ST_QB:
                quien['qb'] = _num(v)
            elif i == _ST_PTS:
                quien['pts'] = _pct_de(v)
    x.update(lf=lf, lc=lc, s=s, c=c, primero=None)


def _con_detalle(ps: List[Dict], dep: str) -> List[Dict]:
    with ThreadPoolExecutor(HILOS) as ex:
        list(ex.map(lambda x: _detalle(x, dep), ps))
    return ps


def promedios_tenis(ps: List[Dict]) -> Dict:
    jue = [sum(x['lf']) + sum(x['lc']) if x['lf'] else None for x in ps]
    st = lambda k: cd._media([x['s'].get(k) for x in ps])
    out = {'n': len(ps), 'pg': cd._pct([x['gf'] > x['gc'] for x in ps]), 'sf': cd._media([x['gf'] for x in ps]), 'sc': cd._media([x['gc'] for x in ps]),
           'jt': cd._media(jue), 'jf': cd._media([sum(x['lf']) if x['lf'] else None for x in ps]), 'jc': cd._media([sum(x['lc']) if x['lc'] else None for x in ps]),
           's1': cd._pct([(x['lf'][0] > x['lc'][0]) if x['lf'] else None for x in ps]),
           's1j': cd._media([x['lf'][0] + x['lc'][0] if x['lf'] else None for x in ps]),
           's3': cd._pct([x['gf'] + x['gc'] >= 3 for x in ps]), 'ace': st('ace'), 'df': st('df'), 'qb': st('qb'),
           'pts': cd._media([x['s'].get('pts') for x in ps], 2)}
    return {k: v for k, v in out.items() if v is not None}


def promedios_beisbol(ps: List[Dict]) -> Dict:
    out = cd.promedios(ps, 'MLB')
    extra = {'pg': cd._pct([x['gf'] > x['gc'] for x in ps]), 'h15': cd._pct([x['gf'] - x['gc'] >= 2 for x in ps]), 'o95': cd._pct([x['gf'] + x['gc'] > 9.5 for x in ps])}
    out.update({k: v for k, v in extra.items() if v is not None})
    return out


def ultimos(ps: List[Dict], dep: str) -> List:
    out = []
    for x in ps[:cd.N_TABLA]:
        if dep == 'Tenis':
            jue = [int(sum(x['lf'])), int(sum(x['lc']))] if x['lf'] else None
            s1 = [int(x['lf'][0]), int(x['lc'][0])] if x['lf'] else None
            extra = [jue, s1, cd._par(x, 'ace')]
        else:
            extra = [cd._parp(x, 1), cd._parp(x, 3), cd._parp(x, 5)]
        out.append([x['fecha'].strftime('%d/%m'), x['rival'], 1 if x['local'] else 0, int(x['gf']), int(x['gc'])] + extra)
    return out


def _feed_tenis(texto: str) -> List[Dict]:
    """Los partidos individuales terminados del feed de Flashscore. Sets: BA/BB, BC/BD, BE/BF, BG/BH, BI/BJ."""
    out = []
    for bloque in texto.split('~ZA÷')[1:]:
        torneo = bloque.split('¬', 1)[0]
        if 'DOUBLES' in torneo.upper() or 'DOBLES' in torneo.upper():
            continue
        for ev in bloque.split('~AA÷')[1:]:
            c = {}
            for campo in ev.split('¬'):
                k, _, v = campo.partition('÷')
                c.setdefault(k, v)
            try:
                if c.get('AB') != '3' or not c.get('AE') or not c.get('AF'):
                    continue
                gh, ga = float(c['AG']), float(c['AH'])
                f = dt.datetime.fromtimestamp(int(c['AD']), dt.timezone.utc)
            except (KeyError, ValueError):
                continue
            if gh + ga == 0:              # no se jugó (abandono antes de empezar)
                continue
            sh, sa = [], []
            for x, y in (('BA', 'BB'), ('BC', 'BD'), ('BE', 'BF'), ('BG', 'BH'), ('BI', 'BJ')):
                if _num(c.get(x)) is None or _num(c.get(y)) is None:
                    break
                sh.append(_num(c[x])); sa.append(_num(c[y]))
            out.append({'f': f, 'home': c['AE'], 'away': c['AF'], 'idh': c.get('PX'), 'ida': c.get('PY'), 'gh': gh, 'ga': ga, 'sh': sh, 'sa': sa})
    return out


def _partidos_fs() -> List[Dict]:
    if not _FS:
        import requests
        h = {'x-fsign': 'SW9D1eZo', 'Referer': 'https://www.flashscore.com/', 'User-Agent': 'Mozilla/5.0'}
        def dia(o):
            try:
                r = requests.get(FS_DIA % o, headers=h, timeout=25)
                return _feed_tenis(r.text) if r.ok else []
            except Exception as e:
                logger.debug('[365] flashscore %s: %s', o, e)
                return []
        with ThreadPoolExecutor(HILOS) as ex:
            for lote in ex.map(dia, range(0, -FS_DIAS, -1)):
                _FS.extend(lote)
        vistos = {}
        for m in _FS:
            vistos[(m['f'], m['home'], m['away'])] = m
        _FS[:] = list(vistos.values()) or [{}]
    return [m for m in _FS if m]


def historial_fs(nombre: str, antes: dt.datetime) -> List[Dict]:
    """Sus partidos en el feed. Si el nombre casa con dos tenistas distintos («Wang X.»), ninguno: nada de adivinar."""
    import escudos
    out, ids = [], set()
    for m in _partidos_fs():
        if m['f'] >= antes:
            continue
        local = bool(escudos._jugador(nombre, m['home']))
        if not local and not escudos._jugador(nombre, m['away']):
            continue
        ids.add(m['idh'] if local else m['ida'])
        lf, lc = (m['sh'], m['sa']) if local else (m['sa'], m['sh'])
        out.append({'id': None, 'fecha': m['f'], 'local': local, 'gf': m['gh'] if local else m['ga'], 'gc': m['ga'] if local else m['gh'], 'tid': m['idh'] if local else m['ida'],
                    'rid': m['ida'] if local else m['idh'], 'rival': m['away'] if local else m['home'], 'nombre': m['home'] if local else m['away'],
                    'nrival': m['away'] if local else m['home'], 'lf': lf, 'lc': lc, 's': {}, 'c': {}, 'primero': None})
    if len(ids) > 1:
        return []
    return sorted(out, key=lambda z: z['fecha'], reverse=True)


def _contexto_fs(p: Dict, ini: dt.datetime, ahora: dt.datetime) -> Optional[Dict]:
    L, _, V = str(p.get('partido')).partition(' vs ')
    pl, pv = historial_fs(L, ini), historial_fs(V, ini)
    if not pl and not pv:
        return None
    rival = {x['tid'] for x in pv}
    ctx = {'ts': int(ahora.timestamp()), 'fl': cd._forma(pl), 'fv': cd._forma(pv), 'sl': promedios_tenis(pl[:N['Tenis']]) if pl else None, 'sv': promedios_tenis(pv[:N['Tenis']]) if pv else None,
           'ul': ultimos(pl, 'Tenis'), 'uv': ultimos(pv, 'Tenis'),
           'h2h': [[x['fecha'].strftime('%d/%m/%y'), x['nombre'] if x['local'] else x['nrival'], '%d-%d' % ((x['gf'], x['gc']) if x['local'] else (x['gc'], x['gf'])),
                    x['nrival'] if x['local'] else x['nombre']] for x in pl if x['rid'] in rival][:5]}
    return {k: v for k, v in ctx.items() if v}


def enfrentamientos(gid, antes: dt.datetime) -> List:
    out = []
    for x in ((_get('games/h2h/', gameId=gid) or {}).get('game') or {}).get('h2hGames') or []:
        f, h, a = _fecha(x.get('startTime')), x.get('homeCompetitor') or {}, x.get('awayCompetitor') or {}
        gh, ga = h.get('score'), a.get('score')
        if f is None or f >= antes or gh is None or ga is None or gh < 0 or ga < 0:
            continue
        out.append((f, [f.strftime('%d/%m/%y'), h.get('name') or '', '%d-%d' % (gh, ga), a.get('name') or '']))
    return [y for _, y in sorted(out, key=lambda z: z[0], reverse=True)][:5]


def contexto(p: Dict, previo: Optional[Dict] = None, ahora: Optional[dt.datetime] = None) -> Optional[Dict]:
    """El contexto, o lo ya publicado si sigue vigente; None si ya se jugó o no se encuentra en 365Scores."""
    try:
        dep = p.get('deporte')
        if dep not in DEPORTES or ' vs ' not in str(p.get('partido') or ''):
            return None
        if not _INICIO:
            _INICIO.append(time.monotonic())
        ahora = ahora or dt.datetime.now(dt.timezone.utc)
        if previo and ahora.timestamp() - float(previo.get('ts') or 0) < VIGENCIA_H * 3600:
            return previo
        ini = _fecha(p.get('inicio')) or ahora
        if ahora - ini > dt.timedelta(hours=8):
            return None
        m = partido365(p)
        al, av = (historial(m['local'].get('id'), ini), historial(m['visita'].get('id'), ini)) if m else ([], [])
        if not al or not av:
            return (_contexto_fs(p, ini, ahora) if dep == 'Tenis' else None) or previo
        pl, pv = _con_detalle(al[:N[dep]], dep), _con_detalle(av[:N[dep]], dep)
        prom = promedios_tenis if dep == 'Tenis' else promedios_beisbol
        ctx = {'ts': int(ahora.timestamp()), 'fl': cd._forma(pl), 'fv': cd._forma(pv), 'sl': prom(pl), 'sv': prom(pv), 'ul': ultimos(pl, dep), 'uv': ultimos(pv, dep),
               'h2h': enfrentamientos(m['g'].get('id'), ini)}
        return {k: v for k, v in ctx.items() if v}
    except Exception as e:
        logger.warning('[365] %s: %s', p.get('partido'), e)
        return previo


def publicados() -> Dict:
    """Lo ya calculado en la pasada anterior: {partido: contexto} de tenis y béisbol."""
    out: Dict = {}
    try:
        import requests
        for arch, clave in (('hoy.json', 'picks'), ('analisis.json', 'analisis')):
            r = requests.get(SITIO + arch, timeout=25, headers={'User-Agent': 'Mozilla/5.0'})
            for f in (r.json().get(clave) or []) if r.ok else []:
                if f.get('deporte') in DEPORTES and (f.get('ctx') or {}).get('ts'):
                    out[f.get('partido')] = f['ctx']
    except Exception as e:
        logger.warning('[365] sin lo publicado: %s', e)
    return out
