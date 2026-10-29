#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v463 — CIERRA LOS PICKS QUE SE QUEDARON PENDIENTES.

El usuario: «en Mis picks salen partidos de ayer como en juego… las combinadas ya
van varias veces que te digo que se cierren; tiene que ser en el momento en que
ya tenemos los resultados». Medido el 23-oct: 200 picks de días pasados seguían
«pendiente» en la base (fútbol, NHL, tenis; 10-30 por día). Causa: el exportador
sólo revisa los partidos de HOY y AYER con el cálculo del día; si en ese momento no
tenía el resultado (ligas que su fuente no publica a tiempo), el pick se quedaba
pendiente PARA SIEMPRE: nadie lo volvía a mirar. Y con él, cada combinada que lo
llevaba.

Aquí, en cada pasada, ANTES de subir los picks:
  1. se piden a la base los pendientes de los últimos 10 días que ya debieron terminar;
  2. el resultado final sale de ESPN (si el pick tiene su partido de ESPN) y, si no,
     del feed de terminados de Flashscore (fútbol y tenis);
  3. se califica con la MISMA regla que la IA (`ia_gemini.liquidar`), con córners y
     tarjetas reales cuando el pick los necesita; si no se puede calificar, se deja;
  4. se pone en la base y en los picks que esta pasada va a subir (para que el
     upsert no lo vuelva a dejar pendiente). Las combinadas se liquidan después.
Sólo con el partido TERMINADO según la fuente. Nunca lanza.
"""
import datetime as dt
import json
import logging
import os
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('liquidar_pendientes')
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/%s/summary'
FS_DIA = 'https://global.flashscore.ninja/2/x/feed/f_%d_%d_3_es-mx_1'
FS_DEP = {'Fútbol': 1, 'Tenis': 2}
DIAS = 15                  # v478 — de 10 a 15: el 27-oct quedaban abiertos picks del 15-oct
ABIERTOS = 'in.(pendiente,vivo)'   # v478 — el exportador deja «vivo» al que empezó; 395 de 462 se quedaban así
# horas desde el inicio para darlo por terminado (si la fuente no dice lo contrario)
DURA = {'Fútbol': 2.5, 'NHL': 3.5, 'NBA': 3.0, 'NFL': 4.0, 'MLB': 4.0, 'Tenis': 4.0}


def _norm(s) -> set:
    t = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.split(r'[^a-z0-9]+', t) if w and w not in ('fc', 'cf', 'sc', 'cd', 'ud', 'club', 'de', 'the', 'afc', 'fk', 'sk', 'ac')}


def _parecido(a, b) -> float:
    x, y = _norm(a), _norm(b)
    return len(x & y) / min(len(x), len(y)) if x and y else 0.0


def _orden(home: str, away: str, a: str, b: str, gh, ga) -> Optional[Tuple]:
    """(goles de A, goles de B) según qué equipo de la fuente es cuál de nuestro «A vs B»."""
    directo, vuelta = _parecido(a, home) + _parecido(b, away), _parecido(a, away) + _parecido(b, home)
    if max(directo, vuelta) < 1.0:
        return None
    return (gh, ga) if directo >= vuelta else (ga, gh)


def _espn(ruta_id: str, a: str, b: str, sesion) -> Optional[Dict]:
    """{g, corners, tarjetas} del partido de ESPN si ya terminó; None si no."""
    try:
        ruta, eid = str(ruta_id).split(':', 1)
        d = sesion.get(ESPN % ruta, params={'event': eid}, timeout=20).json()
        comp = ((d.get('header') or {}).get('competitions') or [{}])[0]
        tipo = (comp.get('status') or {}).get('type') or {}
        if not (tipo.get('completed') or tipo.get('state') == 'post'):
            return None
        cs = comp.get('competitors') or []
        h = next((c for c in cs if c.get('homeAway') == 'home'), None)
        w = next((c for c in cs if c.get('homeAway') == 'away'), None)
        if not h or not w:
            return None
        gh, ga = int(float(h.get('score') or 0)), int(float(w.get('score') or 0))
        # v478 — en copas, la prórroga no cuenta: la casa paga a los 90' (ver `fixtures_espn.marcador_90`)
        prorroga = False
        if tipo.get('name') in ('STATUS_FINAL_AET', 'STATUS_FINAL_PEN', 'STATUS_FINAL_ET', 'STATUS_END_OF_EXTRATIME'):
            import fixtures_espn as fx
            g90 = fx.linescores_90(cs)
            if g90 is None:
                return None
            gh, ga, prorroga = g90[0], g90[1], True
        g = _orden(h['team'].get('displayName'), w['team'].get('displayName'), a, b, gh, ga)
        if g is None:
            return None
        if prorroga:              # córners y tarjetas del boxscore incluyen la prórroga: no se califican
            return {'g': g, 'corners': None, 'tarjetas': None, 'fuente': 'espn'}
        cor, tar = [], []
        for t in ((d.get('boxscore') or {}).get('teams') or []):
            st = {s.get('name'): s.get('displayValue') for s in t.get('statistics') or []}
            try:
                if st.get('wonCorners') is not None:
                    cor.append(int(float(st['wonCorners'])))
                if st.get('yellowCards') is not None:
                    tar.append(int(float(st['yellowCards'])) + int(float(st.get('redCards') or 0)))
            except Exception:
                pass
        return {'g': g, 'corners': sum(cor) if len(cor) == 2 else None, 'tarjetas': sum(tar) if len(tar) == 2 else None, 'fuente': 'espn'}
    except Exception as e:
        logger.debug('[liquidar] espn %s: %s', ruta_id, e)
        return None


_FS: Dict = {}


def _palabras(s) -> List[str]:
    t = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return [w for w in re.split(r'[^a-z0-9]+', t) if w]


def _tenista(nuestro: str, fs: str) -> bool:
    """v478 — ¿«Yushan Shao» es el «Shao Y.» de Flashscore? Los apellidos completos de la fuente
    dentro de nuestro nombre y cada inicial con uno de los nombres que quedan. Dobles, nunca."""
    if '/' in str(fs) or '/' in str(nuestro):
        return False
    t, f = _palabras(nuestro), _palabras(fs)
    llenos, ini = [w for w in f if len(w) > 1], [w for w in f if len(w) == 1]
    if not llenos or any(w not in t for w in llenos):
        return False
    resto = [w for w in t if w not in llenos]
    return all(any(r.startswith(i) for r in resto) for i in ini) and (bool(ini) or not resto or len(llenos) >= 2)


def _feed_fs(dep: int, o: int, sesion) -> List[Dict]:
    k = (dep, o)
    if k not in _FS:
        import resultados_flashscore as rf
        r = sesion.get(FS_DIA % (dep, o), headers={'x-fsign': 'SW9D1eZo', 'Referer': 'https://www.flashscore.com/', 'User-Agent': 'Mozilla/5.0'}, timeout=25)
        _FS[k] = rf._partidos(r.text, '', '') if r.ok else []
    return _FS[k]


def _flashscore_tenis(ini: dt.datetime, a: str, b: str, sesion) -> Optional[Dict]:
    """v478 — el tenis en el feed de Flashscore: nombres «Apellido I.» y los 8 días del feed, del más
    cercano al más lejano (la fecha de los ITF del feed de cuotas va hasta 2 días antes de jugarse).
    Dos tenistas concretos no se enfrentan dos veces en la misma semana."""
    hoy = dt.datetime.now(dt.timezone.utc).date()
    off = (ini.date() - hoy).days
    for o in sorted(range(0, -8, -1), key=lambda x: (abs(x - off), -x)):
        for m in _feed_fs(2, o, sesion):
            if m.get('gh') is None or m.get('ga') is None:
                continue
            if _tenista(a, m['home']) and _tenista(b, m['away']):
                return {'g': (m['gh'], m['ga']), 'corners': None, 'tarjetas': None, 'fuente': 'flashscore'}
            if _tenista(a, m['away']) and _tenista(b, m['home']):
                return {'g': (m['ga'], m['gh']), 'corners': None, 'tarjetas': None, 'fuente': 'flashscore'}
    return None


_TENIS: Dict = {}


def _tenis_liquidador(p: Dict) -> Optional[Dict]:
    """v478 — los resultados de tenis que ya junta el liquidador (ESPN + los CSV del proyecto), con la
    misma protección de `partidos_jugados` contra dos «Wang contra Zhang» distintos en la ventana."""
    try:
        import liquidador as lq
        import partidos_jugados as pj
        if 'res' not in _TENIS:
            hoy = dt.datetime.now(dt.timezone.utc).date()
            _TENIS['res'] = lq._resultados_tenis((hoy - dt.timedelta(days=DIAS + 2)).isoformat(), hoy.isoformat())
        m = pj._marcador_tenis(p, _TENIS['res'])
        if not m:
            m = _tenis_ventana(p, _TENIS['res'], lq)
        return {'g': (int(m[0]), int(m[1])), 'corners': None, 'tarjetas': None, 'fuente': 'liquidador'} if m else None
    except Exception as e:
        logger.debug('[liquidar] tenis %s: %s', p.get('partido'), e)
        return None


VENTANA_TENIS = (-1, 4)    # días: el partido se juega el día del pick o hasta 4 después
FS_BUSCA = 'https://s.livesport.services/api/v2/search/?q={q}&lang-id=1&type-ids=1,2,3,4&project-id=2&project-type-id=1'
FS_JUGADOR = 'https://www.flashscore.com/player/{url}/{pid}/results/'
NO_SE_JUGO_DIAS = 3        # las dos fichas sin el partido a los 3 días → nula (suele ser la fase previa,
                           # que casi nadie publica, o un circuito sin fuente)
SIN_FUENTE_DIAS = 10       # sin ninguna fuente a los 10 días → nula («sin resultado oficial»)
MAX_FICHAS = 150           # picks de tenis por pasada que se buscan por la ficha del jugador
_FICHAS: Dict = {}
_PAGINAS: Dict = {}


def _parecido_ape(a: str, b: str) -> float:
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def _ficha_tenista(nombre: str, sesion) -> Optional[tuple]:
    """v480 — (url, id) del jugador en Flashscore. Todas las palabras de SU nombre tienen que estar (o casi:
    «Neparent»/«Neporent») en el nuestro: «Sora Fukuda» NO es «Fukuda Masahiro»."""
    if nombre in _FICHAS:
        return _FICHAS[nombre]
    t = _palabras(nombre)
    out = None
    for q in ([t[-1], ' '.join(t)] if t else []):
        try:
            cands = sesion.get(FS_BUSCA.format(q=q.replace(' ', '%20')), timeout=15,
                               headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.flashscore.com/'}).json()
        except Exception:
            cands = []
        for x in cands if isinstance(cands, list) else []:
            if (x.get('sport') or {}).get('id') != 2 or (x.get('type') or {}).get('name') != 'Player':
                continue
            fp = _palabras(x.get('name'))
            if fp and len(fp) <= len(t) and all(max(_parecido_ape(w, y) for y in t) >= 0.85 for w in fp):
                out = (x.get('url'), x.get('id'))
                break
        if out:
            break
    _FICHAS[nombre] = out
    return out


def _partidos_tenista(ficha: tuple, sesion) -> List[Dict]:
    if ficha not in _PAGINAS:
        import resultados_flashscore as rf
        out = set()
        try:
            t = sesion.get(FS_JUGADOR.format(url=ficha[0], pid=ficha[1]), timeout=20,
                           headers={'User-Agent': 'Mozilla/5.0'}).text
            for r in rf._registros(t):
                if 'AA' in r and r.get('AE') and r.get('AF') and r.get('AS') in ('1', '2'):
                    try:
                        out.add((dt.datetime.fromtimestamp(int(r['AD']), dt.timezone.utc).date(),
                                 r['AE'], r['AF'], int(r['AG']), int(r['AH'])))
                    except (KeyError, TypeError, ValueError):
                        continue
        except Exception as e:
            logger.debug('[liquidar] ficha %s: %s', ficha, e)
        _PAGINAS[ficha] = [dict(zip(('d', 'h', 'a', 'gh', 'ga'), x)) for x in out]   # la página repite partidos
    return _PAGINAS[ficha]


def _rival(nuestro: str, fs: str) -> bool:
    """El rival, con transliteraciones: el apellido parecido (≥ 0,75) y la inicial igual."""
    if _tenista(nuestro, fs):
        return True
    if '/' in str(fs):
        return False
    t, f = _palabras(nuestro), _palabras(fs)
    llenos, ini = [w for w in f if len(w) > 1], [w for w in f if len(w) == 1]
    if not llenos or not t:
        return False
    ape = max(llenos, key=len)
    mejor = max(t, key=lambda w: _parecido_ape(w, ape))
    return _parecido_ape(mejor, ape) >= 0.75 and (not ini or any(r.startswith(ini[0]) for r in t if r != mejor))


def _tenis_por_jugador(p: Dict, sesion) -> Optional[Dict]:
    """v480 — el tenis que no está en ningún feed (ITF de días pasados): la página de resultados de cada
    jugador en Flashscore, que guarda todos sus partidos. {'g': …} si está; {'nula': 'sin resultado oficial'} si las
    dos fichas existen, ninguna tiene el partido en la ventana y ya pasaron NO_SE_JUGO_DIAS: no hay forma
    de verificarlo (casi siempre la fase previa de un ITF/Challenger, que no se publica) y no se deja «en
    juego» para siempre. None si no se puede saber."""
    a, _, b = str(p.get('partido') or '').partition(' vs ')
    a, b = a.strip(), b.strip()
    try:
        d0 = dt.date.fromisoformat(str(p.get('fecha') or p.get('inicio') or '')[:10])
    except ValueError:
        return None
    fichas, dudoso = 0, False
    for yo, otro, lado in ((a, b, 0), (b, a, 1)):
        fi = _ficha_tenista(yo, sesion)
        if not fi:
            continue
        fichas += 1
        hall = set()
        palabras_otro = [w for w in _palabras(otro) if len(w) > 2]   # el nombre puede venir «Apellido, Nombre»
        for m in _partidos_tenista(fi, sesion):
            if not (VENTANA_TENIS[0] <= (m['d'] - d0).days <= VENTANA_TENIS[1]):
                continue
            if _tenista(yo, m['h']) and _rival(otro, m['a']):
                hall.add((m['gh'], m['ga']))
            elif _tenista(yo, m['a']) and _rival(otro, m['h']):
                hall.add((m['ga'], m['gh']))
            else:
                # un rival medio parecido en la ventana: puede ser el mismo partido mal escrito → no se decide
                suyo = m['a'] if _tenista(yo, m['h']) else m['h']
                if '/' not in suyo and any(_parecido_ape(w, x) >= 0.5 for w in _palabras(suyo) if len(w) > 1 for x in palabras_otro):
                    dudoso = True
        if len(hall) == 1:
            g = hall.pop()
            return {'g': g if lado == 0 else (g[1], g[0]), 'corners': None, 'tarjetas': None, 'fuente': 'flashscore_jugador'}
        if len(hall) > 1:
            return None
    hoy = dt.datetime.now(dt.timezone.utc).date()
    if fichas == 2 and not dudoso and (hoy - d0).days >= NO_SE_JUGO_DIAS:
        return {'nula': 'sin resultado oficial'}
    return None


def _tenis_ventana(p: Dict, res: Dict, lq) -> Optional[tuple]:
    """v480 — el ITF con la fecha corrida: el feed de cuotas fecha el pick al publicarlo y el partido se
    juega hasta 2-3 días después (Golubović–Radenković: pick del 21-oct, jugado el 23). `_marcador_tenis`
    sólo mira ±1 día. Aquí, de −1 a +4, con UN solo ganador en la ventana (dos «Wang contra Zhang» en la
    misma semana no se liquidan) y con sets."""
    a, _, b = str(p.get('partido') or '').partition(' vs ')
    k1, k2 = lq._clave_tenista(a.strip()), lq._clave_tenista(b.strip())
    dia = str(p.get('fecha') or p.get('inicio') or '')[:10]
    if not (k1 and k2 and dia):
        return None
    try:
        d0 = dt.date.fromisoformat(dia)
    except ValueError:
        return None
    dentro = []
    for fecha, r in res.get(tuple(sorted((k1, k2)))) or []:
        try:
            dif = (dt.date.fromisoformat(str(fecha)[:10]) - d0).days
        except ValueError:
            continue
        if VENTANA_TENIS[0] <= dif <= VENTANA_TENIS[1] and r.get('_ganador') in (k1, k2):
            dentro.append(r)
    if not dentro or len({r.get('_ganador') for r in dentro}) > 1:
        return None
    sets = [x for x in (dentro[0].get('sets') or []) if x is not None]
    if len(sets) != 2:
        return None
    hi, lo = max(sets), min(sets)
    return (float(hi), float(lo)) if dentro[0].get('_ganador') == k1 else (float(lo), float(hi))


def _flashscore(deporte: str, ini: dt.datetime, a: str, b: str, sesion) -> Optional[Dict]:
    dep = FS_DEP.get(deporte)
    if not dep:
        return None
    try:
        if deporte == 'Tenis':
            return _flashscore_tenis(ini, a, b, sesion)
        hoy = dt.datetime.now(dt.timezone.utc).date()
        off = (ini.date() - hoy).days
        mejor, puntos = None, 0.0
        for o in (off, off - 1, off + 1):
            if o > 0 or o < -7:
                continue
            for m in _feed_fs(dep, o, sesion):
                p = max(_parecido(a, m['home']) + _parecido(b, m['away']), _parecido(a, m['away']) + _parecido(b, m['home']))
                if p > puntos:
                    puntos, mejor = p, m
        if not mejor or puntos < 1.5:
            return None
        g = _orden(mejor['home'], mejor['away'], a, b, mejor['gh'], mejor['ga'])
        return {'g': g, 'corners': None, 'tarjetas': None, 'fuente': 'flashscore'} if g else None
    except Exception as e:
        logger.debug('[liquidar] flashscore %s vs %s: %s', a, b, e)
        return None


def _utc(s) -> Optional[dt.datetime]:
    try:
        x = dt.datetime.fromisoformat(str(s).replace(' ', 'T').replace('Z', '+00:00'))
        return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def calificar(p: Dict, res: Dict) -> Optional[str]:
    """'verde' / 'roja' con el resultado final; None si la regla no lo puede calificar."""
    import ia_gemini
    a, _, b = str(p.get('partido') or '').partition(' vs ')
    ok = ia_gemini.liquidar(p.get('apuesta'), a.strip(), b.strip(), res['g'], res.get('corners'), res.get('tarjetas'))
    return None if ok is None else ('verde' if ok else 'roja')


def cerrar(locales: List[Dict], url: Optional[str] = None, key: Optional[str] = None, sesion=None) -> int:
    """Cierra los pendientes que ya terminaron. Pone el resultado en la base y en
    `locales` (los picks que esta pasada va a subir). Devuelve cuántos cerró."""
    url, key = url or os.environ.get('SUPABASE_URL'), key or os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return 0
    try:
        import requests
        sesion = sesion or requests.Session()
        H = {'apikey': key, 'Authorization': 'Bearer ' + key}
        ahora = dt.datetime.now(dt.timezone.utc)
        pend = []
        for pag in range(20):          # v478 — por páginas: Supabase entrega 1000 como máximo (v466)
            r = sesion.get(url.rstrip('/') + '/rest/v1/picks', headers=H, timeout=30, params={
                'select': 'id,partido,apuesta,deporte,inicio,fecha,espn,tipo', 'estado': ABIERTOS,
                'inicio': 'gte.' + (ahora - dt.timedelta(days=DIAS)).isoformat(),
                'order': 'id', 'limit': 1000, 'offset': 1000 * pag})
            lote = r.json() if r.ok else []
            pend += lote if isinstance(lote, list) else []
            if not isinstance(lote, list) or len(lote) < 1000:
                break
        pend = [p for p in pend if isinstance(p, dict) and p.get('tipo') not in ('analisis', 'combinada') and ' vs ' in str(p.get('partido') or '')
                and _utc(p.get('inicio')) and ahora - _utc(p['inicio']) > dt.timedelta(hours=DURA.get(p.get('deporte'), 3.0))]
        if not pend:
            return 0
        # el texto real de los premium (el público va tapado)
        ids = [p['id'] for p in pend]
        reales = {}
        for i in range(0, len(ids), 150):
            rp = sesion.get(url.rstrip('/') + '/rest/v1/picks_premium', headers=H, timeout=30,
                            params={'select': 'id,apuesta', 'id': 'in.(%s)' % ','.join(ids[i:i + 150])})
            for x in (rp.json() if rp.ok else []):
                reales[x['id']] = x['apuesta']
        por_partido: Dict = {}
        cerrados = {}
        fichas = 0
        hoy = ahora.date()
        for p in pend:
            p = dict(p, apuesta=reales.get(p['id']) or p.get('apuesta'))
            a, _, b = p['partido'].partition(' vs ')
            k = (p.get('espn') or '', p['partido'], str(p['inicio'])[:10])
            if k not in por_partido:
                res = _espn(p['espn'], a.strip(), b.strip(), sesion) if p.get('espn') else None
                if res is None and p.get('deporte') == 'Tenis':
                    res = _tenis_liquidador(p)
                if res is None:
                    res = _flashscore(p.get('deporte'), _utc(p['inicio']), a.strip(), b.strip(), sesion)
                if res is None and p.get('deporte') == 'Tenis' and fichas < MAX_FICHAS:
                    fichas += 1                       # v480 — la ficha de cada jugador en Flashscore
                    res = _tenis_por_jugador(p, sesion)
                por_partido[k] = res
            res = por_partido[k]
            dias = (hoy - _utc(p['inicio']).date()).days
            if not res and p.get('deporte') == 'Tenis' and dias >= SIN_FUENTE_DIAS:
                res = {'nula': 'sin resultado oficial'}   # v480 — ni ESPN, ni Flashscore, ni BetExplorer
            if not res:
                continue
            if res.get('nula'):
                cerrados[p['id']] = ('nula', res['nula'])
                continue
            e = calificar(p, res)
            if e:
                cerrados[p['id']] = (e, '%d-%d' % tuple(res['g']))
        n = 0
        cuando = ahora.isoformat()
        for pid, (e, marc) in cerrados.items():
            u = sesion.patch(url.rstrip('/') + '/rest/v1/picks', headers=dict(H, Prefer='return=minimal'), timeout=30,
                             params={'id': 'eq.' + pid, 'estado': ABIERTOS}, json={'estado': e, 'marcador': marc, 'actualizado': cuando})
            n += bool(u.ok)
        for f in locales or []:                # que el upsert de esta pasada no lo vuelva a dejar pendiente
            if f.get('id') in cerrados and f.get('estado') in ('pendiente', 'vivo', None):
                f['estado'], f['marcador'] = cerrados[f['id']]
        logger.info('[liquidar] %d pendientes revisados, %d cerrados', len(pend), n)
        return n
    except Exception as e:
        logger.warning('[liquidar] no se cerraron los pendientes: %s', e)
        return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    print('cerrados:', cerrar([]))
