#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v384 — LOS ERRORES DE CUOTA (💰) EN SHARPICKS, Y EL CONTEXTO DE CADA PARTIDO.

El usuario: «cualquier error de cuota que tenga buena probabilidad de acuerdo
a su histórico reciente y los datos de lesiones conviene meterlo… si de 50
errores se ve que 20 se van a cumplir, al gratuito uno o dos y los demás al
VIP».

ERRORES. Los 💰 de la Capa 1 (una casa paga más que el precio justo de
Pinnacle) que pasaron su validación. Cada uno lleva su PROBABILIDAD DE
CUMPLIRSE = la de Pinnacle sin margen (1 / cuota justa) y su VENTAJA (cuánto
paga de más).

v385 — MEDIDO EN 8 AÑOS (`_v385_errores_hist.py`: 13.217 errores de
`pick_ledger.csv`, 2018-2026, dos mitades): se cumplen EXACTAMENTE con la
probabilidad de Pinnacle y, todos juntos, ganan +5,6 / +5,7 por $100 (p5 > 0).
Pierden o no se sostienen: el EMPATE, cuota > 4 y ventaja de sólo 3-5 %. La
forma y el H2H NO mejoran la probabilidad de Pinnacle (AUC 0,667 contra
0,685): el mercado ya los descuenta. Filtro: ventaja ≥ 5 %, probabilidad
≥ 30 %, cuota ≤ 4, nunca empate. Al canal gratis, 1-2 de probabilidad ≥ 55 %
(salen ~7 de 10); al VIP, todos, con 🔥 los patrones más fuertes (local
favorito con ventaja ≥ 5 %: +7 / +16; ventaja ≥ 12 %: +24 / +19).

CONTEXTO. Para cada partido de fútbol: la forma (últimos 5 de cada equipo),
los últimos cruces (H2H) con fecha y marcador, del histórico de Flashscore
(los mismos nombres de equipo que los errores), y las bajas de FotMob cuando
las hay. Se enseña en la tarjeta y se guarda para volver a medirlo.
Nunca lanza.
"""
import datetime as dt
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger('errores_web')
VENTAJA_MIN = 0.05
PROB_MIN = 0.30
CUOTA_MAX = 4.0
PROB_GRATIS = 0.55
N_GRATIS = 2
HORAS_GRATIS = 24


def _f(x) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _hora(x) -> str:
    """La hora de inicio en «AAAA-MM-DD HH:MM:SS» (UTC). Algunos errores de
    cuota la traen en segundos desde 1970 («1792242000»): Supabase rechazaba
    el lote ENTERO de 200 por uno así (v389, 17-oct)."""
    s = str(x or '').strip()
    if s.replace('.', '', 1).isdigit():
        try:
            return dt.datetime.fromtimestamp(float(s), dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return ''
    return s.replace('T', ' ')[:19]


def _resultados_anunciados(ruta: str = 'anunciadas_dia.json') -> Dict:
    """(partido, apuesta) → (resultado, marcador) de los 💰 ya liquidados."""
    out = {}
    try:
        d = json.load(open(ruta, encoding='utf-8'))
        for e in (d.get('partidos') or {}).values():
            for c in e.get('capa1') or []:
                if c.get('nivel') == '💰' and c.get('resultado'):
                    out[(e.get('partido'), c.get('apuesta'))] = (c['resultado'], c.get('marcador'))
    except Exception as ex:
        logger.debug('[errores] anunciadas: %s', ex)
    return out


def errores(datos: Dict, ahora: Optional[dt.datetime] = None) -> List[Dict]:
    """Los 💰 del día como filas del sitio (`tipo` = 'error'), con su
    probabilidad, su ventaja, si pasan el filtro y cuáles van al gratis."""
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    res = _resultados_anunciados()
    out = []
    for c in (datos or {}).get('capa1') or []:
        try:
            if c.get('validado') is False or 'Pinnacle' not in str(c.get('origen') or ''):
                continue
            cuota, justa = _f(c.get('cuota')), _f(c.get('cuota_justa')) or _f(c.get('pinnacle'))
            if not cuota or not justa:
                continue
            prob, ventaja = 1.0 / justa, cuota / justa - 1.0
            ap = str(c.get('apuesta') or '')
            if ventaja < VENTAJA_MIN or prob < PROB_MIN or cuota > CUOTA_MAX or 'mpate' in ap:
                continue
            # 🔥 los patrones más fuertes medidos en 8 años
            local = c.get('lado') == 'home' and ' vs ' in str(c.get('partido') or '')
            fuerte = ventaja >= 0.12 or (local and prob >= 0.45)
            r = res.get((c.get('partido'), c.get('apuesta')))
            estado = {'verde': 'verde', 'rojo': 'roja'}.get((r or ('',))[0], 'pendiente')
            out.append({'partido': c.get('partido'), 'inicio': _hora(c.get('inicio')),
                        'fecha': c.get('fecha'), 'deporte': c.get('deporte'), 'liga': c.get('liga'),
                        'clave_liga': c.get('clave_liga'),
                        'apuesta': c.get('apuesta'), 'cuota': round(cuota, 3), 'prob': round(prob, 3),
                        'elige': False, 'tipo': 'error', 'casa': c.get('casa'), 'ventaja': round(ventaja, 3),
                        'porque': ('🔥 ' if fuerte else '') + 'Paga %.0f %% más que el precio justo (Pinnacle) en %s' % (100 * ventaja, c.get('casa') or 'la casa'),
                        'estado': estado, 'resultado_c1': None, 'marcador': (r or (None, None))[1], 'gratis': False})
        except Exception as ex:
            logger.debug('[errores] %s: %s', c.get('partido'), ex)
    # v386 — UNO POR PARTIDO: en «Gomora vs Cape Town City» pasaban los dos
    # lados (uno pierde seguro) y «Ayr vs Partick» salía con dos nombres. Se
    # queda el más probable. Medido (9-16 oct): 134 → 127, 54 → 57 %.
    import re
    def _k(p):
        a, _, b = str(p.get('partido') or '').partition(' vs ')
        n = lambda t: re.sub(r'[^a-z]', '', t.lower())[:5]
        return (str(p.get('fecha')), n(a), n(b))
    mejor = {}
    for p in out:
        k = _k(p)
        if k not in mejor or p['prob'] > mejor[k]['prob']:
            mejor[k] = p
    out = list(mejor.values())
    # al gratis: los más probables de las próximas horas (uno por partido)
    fin = ahora + dt.timedelta(hours=HORAS_GRATIS)
    vistos = set()
    for p in sorted(out, key=lambda x: -x['prob']):
        try:
            ini = dt.datetime.fromisoformat(p['inicio']).replace(tzinfo=dt.timezone.utc)
        except Exception:
            continue
        if p['estado'] == 'pendiente' and p['prob'] >= PROB_GRATIS and ahora < ini <= fin and p['partido'] not in vistos:
            p['gratis'] = True
            vistos.add(p['partido'])
            if len(vistos) >= N_GRATIS:
                break
    return out


# ---------- contexto: forma, H2H y bajas ----------
_FS = {}


def _flashscore():
    if 'df' not in _FS:
        try:
            import pandas as pd
            fs = [pd.read_csv(f) for f in ('resultados_flashscore.csv.gz', 'resultados_flashscore_reciente.csv.gz')
                  if os.path.exists(f)]
            df = pd.concat(fs).drop_duplicates('match_id') if fs else None
            if df is not None:
                df['date'] = pd.to_datetime(df['ini'], errors='coerce')
                df = df.dropna(subset=['date', 'gh', 'ga']).sort_values('date')
                idx = {}
                for i, (h, a) in enumerate(zip(df['home'], df['away'])):
                    idx.setdefault(h, []).append(i)
                    idx.setdefault(a, []).append(i)
                _FS.update(df=df, idx=idx)
            else:
                _FS.update(df=None, idx={})
        except Exception as ex:
            logger.debug('[errores] flashscore: %s', ex)
            _FS.update(df=None, idx={})
    return _FS['df'], _FS['idx']


def _bajas() -> Dict:
    if 'bajas' not in _FS:
        m = {}
        try:
            d = json.load(open('bajas_dia.json', encoding='utf-8'))
            for e in (d.get('partidos') or {}).values():
                for lado in ('home', 'away'):
                    x = e.get(lado) or {}
                    if x.get('equipo'):
                        m[x['equipo']] = [b.get('jugador') for b in x.get('bajas') or [] if b.get('jugador')]
        except Exception:
            pass
        _FS['bajas'] = m
    return _FS['bajas']


def _forma(df, idx, eq, antes) -> str:
    filas = [i for i in idx.get(eq, [])]
    if not filas:
        return ''
    m = df.iloc[filas]
    m = m[m['date'] < antes].tail(5)
    out = ''
    for h, gh, ga in zip(m['home'], m['gh'], m['ga']):
        gf, gc = (gh, ga) if h == eq else (ga, gh)
        out += 'G' if gf > gc else ('E' if gf == gc else 'P')
    return out


def _norm(t) -> str:
    """Para empatar nombres parecidos entre fuentes («Sociedad B» / «Real Sociedad B»)."""
    import re
    import unicodedata
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().lower()
    pal = [w for w in re.split(r'[^a-z0-9]+', t) if w and w not in ('fc', 'cf', 'sc', 'cd', 'ud', 'club', 'real', 'de', 'the', 'afc', 'sd')]
    return ' '.join(pal)


def _equipo_fs(nombre, idx) -> Optional[str]:
    """El nombre de Flashscore de un equipo: exacto o, si no, el parecido."""
    if nombre in idx:
        return nombre
    n = _norm(nombre)
    if not n:
        return None
    if 'norm' not in _FS:
        _FS['norm'] = {}
        for k in idx:
            _FS['norm'].setdefault(_norm(k), k)
    return _FS['norm'].get(n)


def _promedios(h, eq, antes, n=10) -> Optional[Dict]:
    """v391 — lo de los últimos `n` partidos del equipo en el histórico de la liga."""
    import pandas as pd
    m = h[((h['home_team'] == eq) | (h['away_team'] == eq)) & (h['date'] < antes)].sort_values('date').tail(n)
    if len(m) < 3:
        return None
    out = {'n': int(len(m))}
    def lado(col):
        a = pd.to_numeric(m['home_' + col], errors='coerce').where(m['home_team'] == eq, pd.to_numeric(m['away_' + col], errors='coerce'))
        b = pd.to_numeric(m['away_' + col], errors='coerce').where(m['home_team'] == eq, pd.to_numeric(m['home_' + col], errors='coerce'))
        return a, b
    gf, gc = lado('goals')
    out['gf'], out['gc'] = round(float(gf.mean()), 2), round(float(gc.mean()), 2)
    tot = gf + gc
    out['o25'] = round(float((tot > 2.5).mean()), 2)
    out['btts'] = round(float(((gf > 0) & (gc > 0)).mean()), 2)
    for col, k in (('corners', 'cor'), ('shots_on', 'tap'), ('yellow', 'tar'), ('possession', 'pos')):
        if 'home_' + col in m.columns:
            a, _ = lado(col)
            if a.notna().sum() >= 3:
                out[k] = round(float(a.mean()), 1)
    # v464 — el usuario: «tenemos tiros a puerta, pero hacen falta los tiros»: a puerta + desviados
    if 'home_shots_on' in m.columns and 'home_shots_off' in m.columns:
        on, _ = lado('shots_on')
        off, _ = lado('shots_off')
        tot = on + off
        if tot.notna().sum() >= 3:
            out['tir'] = round(float(tot.mean()), 1)
    res = ['G' if a > b else ('E' if a == b else 'P') for a, b in zip(gf, gc)]
    out['forma'] = ''.join(res[-5:])
    return out


_MEMO_REALES: Dict = {}


def _ultimos(h, eq, antes, clave, n=5) -> Optional[List]:
    """v492 — LOS ÚLTIMOS 5 PARTIDOS DE VERDAD, NO EL PROMEDIO. El usuario: «que tenga las estadísticas
    más importantes de sus últimos 5 partidos, no en promedio sino las reales». Del más reciente al más
    viejo: [fecha, rival, local (1/0), goles a favor, en contra, [córners a favor, en contra],
    [a puerta…], [amarillas…]]. Córners, tiros y tarjetas sólo de las filas OBSERVADAS
    (`_solo_reales`, v392): las que escribió el generador salen como None («—»), nunca un número falso."""
    import pandas as pd
    m = h[((h['home_team'] == eq) | (h['away_team'] == eq)) & (h['date'] < antes)].sort_values('date').tail(n)
    if not len(m):
        return None
    k = (clave, len(h))
    if k not in _MEMO_REALES:
        try:
            import rendimiento_equipos as _re
            _MEMO_REALES[k] = {c: set(_re._solo_reales(h, c).index) for c in ('corners', 'shots_on', 'yellow')}
        except Exception:
            _MEMO_REALES[k] = {}
    reales = _MEMO_REALES[k]

    def par(row, col, loc):
        a, b = row.get('home_' + col), row.get('away_' + col)
        if row.name not in reales.get(col, ()) or pd.isna(a) or pd.isna(b):
            return None
        a, b = int(a), int(b)
        return [a, b] if loc else [b, a]
    out = []
    for _, r in m.iloc[::-1].iterrows():
        if pd.isna(r['home_goals']) or pd.isna(r['away_goals']):
            continue
        loc = r['home_team'] == eq
        gf, gc = (int(r['home_goals']), int(r['away_goals'])) if loc else (int(r['away_goals']), int(r['home_goals']))
        out.append([r['date'].strftime('%d/%m'), str(r['away_team'] if loc else r['home_team']), 1 if loc else 0, gf, gc,
                    par(r, 'corners', loc), par(r, 'shots_on', loc), par(r, 'yellow', loc)])
    return out or None


def _promedios_fs(df, idx, eq, antes, n=10) -> Optional[Dict]:
    """v464 — cuando la liga no tiene histórico propio (4.ª checa, Copa Santa Catarina…):
    lo de sus últimos `n` partidos en los resultados de Flashscore (sólo goles: es lo que hay)."""
    filas = idx.get(eq, []) if idx else []
    if not filas:
        return None
    m = df.iloc[filas]
    m = m[m['date'] < antes].tail(n)
    if len(m) < 3:
        return None
    gf = [gh if h == eq else ga for h, gh, ga in zip(m['home'], m['gh'], m['ga'])]
    gc = [ga if h == eq else gh for h, gh, ga in zip(m['home'], m['gh'], m['ga'])]
    k = len(gf)
    return {'n': k, 'gf': round(sum(gf) / k, 2), 'gc': round(sum(gc) / k, 2),
            'o25': round(sum(1 for a, b in zip(gf, gc) if a + b > 2.5) / k, 2),
            'btts': round(sum(1 for a, b in zip(gf, gc) if a > 0 and b > 0) / k, 2),
            'forma': ''.join('G' if a > b else ('E' if a == b else 'P') for a, b in zip(gf, gc))[-5:]}


def _con_sus_ligas(h, clave: str, equipos) -> 'pd.DataFrame':
    """v415 — LOS PARTIDOS DE LA COMPETICIÓN + LOS DE LA LIGA DE CADA EQUIPO.

    El usuario: «Como vs Manchester United no trae las estadísticas ni el H2H
    que tienen los otros… quiero que todos tengan, no estimaciones: datos
    reales». En la Champions, Como tenía 2 partidos en el histórico (con menos
    de 3 no se calcula nada) y los últimos 10 del United eran de temporadas
    viejas. Pero los dos tienen cientos de partidos REALES y al día en su liga
    (Serie A, Premier), con córners, tiros y tarjetas. Aquí se juntan: los de
    esta competición y los de la liga de cada equipo (`catalogo_equipos`), con
    el nombre del equipo unificado; `_promedios` toma los 10 más recientes.
    En un partido de liga no cambia nada (su liga es la misma).
    """
    import pandas as pd
    partes = [h] if h is not None and len(h) else []
    for eq in equipos:
        try:
            import catalogo_equipos as ce
            r = ce.nombre_en_su_liga(eq)
            liga = r[0] if r else ce.liga_de(eq)
        except Exception:
            r, liga = None, None
        if not liga or liga == clave:
            continue
        try:
            import panel_equipos as pe
            d = pe._historico(liga)
        except Exception:
            d = None
        if d is None or not len(d):
            continue
        nom = r[1] if r else None
        if not nom:
            # el catálogo sabe su liga pero no cómo se llama ahí («Man United»):
            # el traductor del proyecto, SÓLO contra los equipos de esa liga
            try:
                import name_mapper as nm
                nom = nm.mapear(eq, set(d['home_team']) | set(d['away_team']), contexto='contexto ' + liga)
            except Exception:
                nom = None
        if not nom:
            continue
        d = d[(d['home_team'] == nom) | (d['away_team'] == nom)].copy()
        if nom != eq:
            d['home_team'] = d['home_team'].replace(nom, eq)
            d['away_team'] = d['away_team'].replace(nom, eq)
        partes.append(d)
    if not partes:
        return h
    out = pd.concat(partes, ignore_index=True, sort=False)
    out['date'] = pd.to_datetime(out['date'], errors='coerce', utc=True).dt.tz_localize(None)
    return out.drop_duplicates(subset=['date', 'home_team', 'away_team'])


# v477 — el usuario, con Atlético de San Luis vs América: «no puede ser que Playdoit no cotice; tiene que
# salir el parley en todos los partidos». `mercado_dia.json` sólo trae los partidos del precálculo de
# los próximos 2 días: 69 de 248 partidos se quedaban sin la casa (Inter-Fiorentina, Celta-Betis,
# PSG-Lyon, toda la Liga MX Femenil…). Ahora, si no está ahí, se pide a Playdoit en vivo (sólo en la
# pasada del exportador: `RED_CASA`), y si su buscador no lo halla («PSG», «Tigres de la UANL (F)»)
# se busca en su catálogo con el emparejador de los escudos (misma categoría, ±3 h).
RED_CASA = False
_CASA_MEM: Dict = {}


# cómo abrevia la casa a los que el proyecto escribe de otra forma (el buscador de Playdoit no los casa)
_ABREV_CASA = {'psg': 'Paris Saint-Germain', 'paris saint germain': 'Paris Saint-Germain', 'olympique lyonnais': 'Lyon',
               'olympique marseille': 'Marseille', 'olympique de marseille': 'Marseille', 'inter milan': 'Inter', 'ac milan': 'Milan'}


def _limpio(n: str) -> str:
    import re
    t = re.sub(r'\s*\((F|W)\)|\s+(Women|Femenil|Fem|W)$', '', str(n or '')).strip()
    return _ABREV_CASA.get(t.lower(), t)


_LADOS = (('goles_home', 'goles_away'), ('corners_home', 'corners_away'), ('remates_home', 'remates_away'),
          ('remates_on_home', 'remates_on_away'), ('tarjetas_home', 'tarjetas_away'))


def _girar(tab: Dict) -> Dict:
    t = dict(tab)
    for x, y in _LADOS:
        t[x], t[y] = tab.get(y), tab.get(x)
    if isinstance(tab.get('1x2'), dict):
        t['1x2'] = dict(tab['1x2'], home=tab['1x2'].get('away'), away=tab['1x2'].get('home'))
    return {k: v for k, v in t.items() if v is not None}


def playdoit_en_vivo(home: str, away: str, inicio=None, liga: str = '') -> Dict:
    """El tablero de Playdoit pedido en el momento ({} si no lo cotiza)."""
    k = (home, away, str(inicio)[:13], liga)
    if k in _CASA_MEM:
        return _CASA_MEM[k]
    tab = {}
    try:
        import cuotas_multi as cm
        import escudos
        import mercado_implicito as mi
        r, girado = cm.mercados_playdoit('futbol', home, away), False
        cat = escudos._cat(liga, home, away)
        if r and escudos._cat(r.get('liga'), r.get('home'), r.get('away')) != cat:
            r = None                    # su buscador dio el FEMENIL del Cruz Azul-Toluca varonil: no sirve
        if not r:
            ini = escudos._utc(inicio)
            mejor, pts = None, 0.0
            for e in (cm._indice_pdt('futbol') or {}).values():
                fe = escudos._utc(e.get('fecha'))
                if ini and (not fe or abs((fe - ini).total_seconds()) > 3 * 3600):
                    continue
                if escudos._cat(e.get('liga'), e.get('home'), e.get('away')) != cat:
                    continue
                eh, ea = _limpio(e.get('home')), _limpio(e.get('away'))
                for g, x in ((False, escudos._puntos(home, away, eh, ea, True)), (True, escudos._puntos(home, away, ea, eh, True))):
                    if x > pts:
                        mejor, pts, girado = e, x, g
            if mejor and pts >= 0.8:
                r = cm.mercados_playdoit('futbol', mejor['home'], mejor['away'])
        if r:
            tab = mi.del_tablero(r) or {}
            if girado:
                tab = _girar(tab)
    except Exception as e:
        logger.debug('[errores] Playdoit en vivo %s-%s: %s', home, away, e)
        tab = {}
    _CASA_MEM[k] = tab
    return tab


def casa_del_partido(home: str, away: str, clave: Optional[str], inicio=None, liga: str = '') -> Dict:
    """v474 — el tablero de Playdoit del partido. Primero por la llave de los nombres; si la casa lo
    llama distinto («1. FC Nurnberg» / «Nurnberg»), se busca en SU MISMA liga con el emparejador de los
    escudos (alias del proyecto y parecido, nunca «contiene»); v477 — y si no está en el fichero del
    día, se pide en vivo. {} si no lo cotiza."""
    try:
        import mercado_implicito as mi
        t = mi.del_partido(home, away)
        if t:
            return t
        import escudos
        mejor, pts = None, 0.0
        for v in (mi.cargar().get('partidos') or {}).values():
            if clave and v.get('clave_liga') and v.get('clave_liga') != clave:
                continue
            x = escudos._puntos(home, away, str(v.get('home') or ''), str(v.get('away') or ''), True)
            if x > pts:
                mejor, pts = v, x
        if mejor and pts >= 0.8:
            return dict(mejor)
    except Exception as e:
        logger.debug('[errores] casa %s-%s: %s', home, away, e)
    return playdoit_en_vivo(home, away, inicio, liga) if RED_CASA else {}


def contexto(p: Dict) -> Optional[Dict]:
    """{'fl': 'GGEPG', 'fv': ..., 'sl'/'sv': promedios de los últimos 10, 'h2h': [[fecha, local, marcador, visita], …], 'bl': [...], 'bv': [...]}"""
    try:
        if str(p.get('deporte') or '') != 'Fútbol' or ' vs ' not in str(p.get('partido') or ''):
            return None
        home, away = [s.strip() for s in str(p['partido']).split(' vs ', 1)]
        df, idx = _flashscore()
        import pandas as pd
        antes = pd.Timestamp(str(p.get('inicio') or '')[:10] or dt.date.today().isoformat())
        ctx = {}
        # v391 — 1.º el histórico de la LIGA (mismos nombres que el pick, y con
        # córners, tiros, tarjetas, posesión); 2.º Flashscore con nombres parecidos
        clave = p.get('clave_liga')
        if clave:
            try:
                import panel_equipos as pe
                h = _con_sus_ligas(pe._historico(clave), clave, (home, away))   # v415
                if h is not None and len(h):
                    h = h.copy()
                    h['date'] = pd.to_datetime(h['date'], errors='coerce', utc=True).dt.tz_localize(None)
                    pl, pv = _promedios(h, home, antes), _promedios(h, away, antes)
                    if pl:
                        ctx['sl'], ctx['fl'] = pl, pl['forma']
                    if pv:
                        ctx['sv'], ctx['fv'] = pv, pv['forma']
                    # v492 — y sus últimos 5 partidos, uno por uno
                    ul, uv = _ultimos(h, home, antes, clave), _ultimos(h, away, antes, clave)
                    if ul:
                        ctx['ul'] = ul
                    if uv:
                        ctx['uv'] = uv
                    # v470 — líneas por estadística con su probabilidad medida (va en el análisis IA)
                    try:
                        import lineas_stats
                        casa = casa_del_partido(home, away, clave, p.get('inicio'), p.get('liga') or '')   # Playdoit (v472/v474/v477)
                        lin = lineas_stats.calcular(h, home, away, antes, casa)
                        if lin:
                            ctx['lin'] = lin
                    except Exception as ex:
                        logger.debug('[errores] líneas %s: %s', p.get('partido'), ex)
                    c = h[(((h.home_team == home) & (h.away_team == away)) | ((h.home_team == away) & (h.away_team == home))) & (h['date'] < antes)]
                    c = c.sort_values('date').tail(5)
                    if len(c):
                        ctx['h2h'] = [[d.strftime('%d/%m/%y'), a, '%d-%d' % (gh, ga), b] for d, a, gh, ga, b in
                                      zip(c['date'], c['home_team'], c['home_goals'], c['away_goals'], c['away_team'])
                                      if pd.notna(gh) and pd.notna(ga)][::-1]
            except Exception as ex:
                logger.debug('[errores] liga %s: %s', clave, ex)
        if df is not None:
            hf, af = _equipo_fs(home, idx) or home, _equipo_fs(away, idx) or away
            if not ctx.get('fl'):
                ctx['fl'] = _forma(df, idx, hf, antes)
            if not ctx.get('fv'):
                ctx['fv'] = _forma(df, idx, af, antes)
            # v464 — el usuario: «que TODOS tengan estadísticas, aunque no se hayan enfrentado»
            if not ctx.get('sl'):
                ctx['sl'] = _promedios_fs(df, idx, hf, antes)
            if not ctx.get('sv'):
                ctx['sv'] = _promedios_fs(df, idx, af, antes)
            comun = sorted(set(idx.get(hf, [])) & set(idx.get(af, []))) if len(ctx.get('h2h') or []) < 2 else []
            if comun:
                m = df.iloc[comun]
                m = m[m['date'] < antes].tail(5)
                ctx['h2h'] = [[d.strftime('%d/%m/%y'), h, '%d-%d' % (gh, ga), a]
                              for d, h, gh, ga, a in zip(m['date'], m['home'], m['gh'], m['ga'], m['away'])][::-1]
        # v477 — el parley EN TODOS los partidos que la casa cotiza: sin histórico de la liga, con la casa sola
        if not ctx.get('lin'):
            try:
                import lineas_stats
                sc = lineas_stats.solo_casa(casa_del_partido(home, away, clave, p.get('inicio'), p.get('liga') or ''))
                if sc:
                    ctx['lin'] = sc
            except Exception as ex:
                logger.debug('[errores] casa sola %s: %s', p.get('partido'), ex)
        b = _bajas()
        if b.get(home):
            ctx['bl'] = b[home][:6]
        if b.get(away):
            ctx['bv'] = b[away][:6]
        return {k: v for k, v in ctx.items() if v} or None   # (fl, fv, sl, sv, h2h, bl, bv)
    except Exception as ex:
        logger.debug('[errores] contexto %s: %s', p.get('partido'), ex)
        return None
