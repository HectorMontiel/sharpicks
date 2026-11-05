# -*- coding: utf-8 -*-
"""
v558 — EL MÉTODO DEL USUARIO PARA ARMAR PARLEYS, EN CUALQUIER PARTIDO QUE COTICE PLAYDOIT.

Por cada línea de la casa se cuenta en cuántos de los últimos 10 y últimos 5 partidos se habría cumplido, viendo lo
del equipo y lo que concede el rival (en los totales, el total de los partidos de cada uno). La página toma las patas
de más cumplimiento, una por estadística.

Medido el 5-nov-2026 en 3.452 partidos y 154.531 líneas (D:/Claude/mediciones/medir_parley_usuario*.py). Con
cumplimiento de 80 %+ y cuota total 1,5-3,2 rinde −0,4 a −3,8 por $100 con 2 patas y −0,5 a −3,5 con 3, contra −12 a
−19 eligiendo por la casa. NO está probado que gane dinero y el cálculo es a producto de cuotas: el Constructor real
puede pagar menos. Con 4 patas no es estable.
"""
from typing import Dict, List, Optional

# clave del tablero -> (familia, lado, columna del histórico)
MERCADOS = {
    'goles': ('goles', 't', 'goals'), 'goles_home': ('goles', 'h', 'goals'), 'goles_away': ('goles', 'a', 'goals'),
    'corners': ('corners', 't', 'corners'), 'corners_home': ('corners', 'h', 'corners'), 'corners_away': ('corners', 'a', 'corners'),
    'tarjetas': ('tarjetas', 't', 'tarjetas'), 'tarjetas_home': ('tarjetas', 'h', 'tarjetas'), 'tarjetas_away': ('tarjetas', 'a', 'tarjetas'),
    'remates_on': ('a_puerta', 't', 'shots_on'), 'remates_on_home': ('a_puerta', 'h', 'shots_on'), 'remates_on_away': ('a_puerta', 'a', 'shots_on'),
    'remates': ('remates', 't', 'tiros'), 'remates_home': ('remates', 'h', 'tiros'), 'remates_away': ('remates', 'a', 'tiros'),
}
# v362 y v558: bajo «corners» y otras claves vienen líneas de OTRO mercado («más de 1,5» a 2,12 acierta 100 %).
MIN_LINEA = {'corners': 5.5, 'corners_home': 1.5, 'corners_away': 1.5, 'tarjetas': 1.5, 'tarjetas_home': 0.5, 'tarjetas_away': 0.5,
             'remates': 12.5, 'remates_home': 5.5, 'remates_away': 4.5, 'remates_on': 4.5, 'remates_on_home': 1.5, 'remates_on_away': 1.5,
             'goles': 0.5, 'goles_home': 0.5, 'goles_away': 0.5}
CUOTA_MIN, CUOTA_MAX = 1.10, 2.20       # el rango medido por pata
MIN_PARTIDOS = 5                        # de cada equipo, para que sea el método medido; con menos, el cumplimiento se
                                        # encoge hacia la probabilidad de la casa y la página avisa «poca historia»
POR_LADO = 2                            # candidatas por estadística y lado (equipo A, equipo B, partido): así los totales no
                                        # tapan a las de equipo; la 2.ª es la de repuesto del botón de cambiar


def escalera_limpia(clave: str, tabla) -> List[tuple]:
    """(línea, prob. de «más», entrada) coherentes: más alta la línea, menor la probabilidad."""
    if not isinstance(tabla, dict):
        return []
    ent = []
    for k, x in tabla.items():
        if not isinstance(x, dict):             # fotos viejas: sólo la prob., sin cuota
            continue
        try:
            lin, p = float(k), float(x.get('p'))
        except (TypeError, ValueError):
            continue
        if lin % 1 == 0.5 and 0.02 < p < 0.98 and lin >= MIN_LINEA.get(clave, 0):
            ent.append((lin, p, x))
    ent.sort(key=lambda z: -z[0])
    out, prev = [], 0.0
    for lin, p, x in ent:
        if p < prev - 0.03:                     # bajó la línea y bajó la probabilidad: es de otro mercado
            continue
        prev = max(prev, p)
        out.append((lin, p, x))
    return out


def _partidos(h):
    """El histórico con las columnas del método; sólo estadísticas observadas."""
    import pandas as pd
    d = h
    extra = {}
    for s in ('home', 'away'):
        num = lambda c: pd.to_numeric(d[c], errors='coerce') if c in d.columns else None
        am, ro, on, off = num(s + '_yellow'), num(s + '_red'), num(s + '_shots_on'), num(s + '_shots_off')
        if am is not None:
            extra[s + '_tarjetas'] = am + ro if ro is not None else am
        if on is not None and off is not None:
            extra[s + '_tiros'] = on + off
    return d.assign(**extra) if extra else d


def _reales(d):
    """Sólo filas con estadística observada. Los goles NO pasan por aquí: siempre son reales, y filtrarlos por los córners
    dejaba sin historia a equipos como Mechelen, cuyos córners no llegan de ESPN."""
    import rendimiento_equipos as re_
    try:
        return re_._solo_reales(d, 'home_corners')
    except Exception:
        return d


def _ventana(d, eq: str, st: str, tipo: str, n: int = 10):
    """Últimos n valores del equipo. tipo: f = a favor, c = en contra, t = total del partido."""
    import pandas as pd
    hc, ac = 'home_' + st, 'away_' + st
    if hc not in d.columns or ac not in d.columns:
        return []
    x = d[(d.home_team == eq) | (d.away_team == eq)]
    f = pd.to_numeric(x[hc].where(x.home_team == eq, x[ac]), errors='coerce')
    c = pd.to_numeric(x[ac].where(x.home_team == eq, x[hc]), errors='coerce')
    v = f if tipo == 'f' else c if tipo == 'c' else f + c
    return [float(a) for a in v.dropna().tolist()][-n:]


def _cumple(vals: List[float], dire: str, lin: float) -> List[bool]:
    return [a > lin if dire == 'mas' else a < lin for a in vals]


def pozo(h, home: str, away: str, antes, mercado: Optional[Dict]) -> Optional[List[list]]:
    """Las patas candidatas, de más a menos cumplimiento:
    [familia, lado (h|a|t), más|menos, línea, cuota, prob. casa, score, c10, n10, c5, n5, mínimo, máximo, completa, promedio].
    c10/n10 y c5/n5 cuentan los dos equipos juntos; mínimo, máximo y promedio, de esos últimos 10. La página enseña el promedio:
    predice mejor que la mediana (medir_media_mediana.py, 98 mil equipo-partido: 14 de 15 líneas, p5>0 en las dos mitades).
    completa = 0 si a algún equipo le
    faltan partidos (rivales de ligas que no tenemos, como Egnatia): el usuario lo pidió en TODO partido que cotice la casa."""
    if not mercado:
        return None
    todo = _partidos(h[h['date'] < antes].sort_values('date')) if h is not None and len(h) else None
    obs = _reales(todo) if todo is not None else None
    filas: Dict[str, List[list]] = {}
    for clave, (fam, lado, st) in MERCADOS.items():
        lineas = escalera_limpia(clave, mercado.get(clave))
        if not lineas:
            continue
        d = todo if st == 'goals' else obs
        if d is None:
            a, b = [], []
        elif lado == 't':
            a, b = _ventana(d, home, st, 't'), _ventana(d, away, st, 't')
        else:
            eq, riv = (home, away) if lado == 'h' else (away, home)
            a, b = _ventana(d, eq, st, 'f'), _ventana(d, riv, st, 'c')
        completa = len(a) >= MIN_PARTIDOS and len(b) >= MIN_PARTIDOS
        for lin, p, x in lineas:
            for dire, cu, pc in (('mas', x.get('mas'), p), ('menos', x.get('menos'), 1 - p)):
                try:
                    cu = float(cu)
                except (TypeError, ValueError):
                    continue
                if not CUOTA_MIN <= cu <= CUOTA_MAX:
                    continue
                ca, cb, ca5, cb5 = _cumple(a, dire, lin), _cumple(b, dire, lin), _cumple(a[-5:], dire, lin), _cumple(b[-5:], dire, lin)
                if completa:
                    # el score medido: cada ventana pesa igual a su tamaño nominal, con 1 acierto y 1 fallo de suavizado
                    score = (10 * (sum(ca) / len(ca) + sum(cb) / len(cb)) + 5 * (sum(ca5) / len(ca5) + sum(cb5) / len(cb5)) + 1) / 32
                else:
                    score = (sum(ca) + sum(cb) + 5 * pc) / (len(ca) + len(cb) + 5)
                filas.setdefault(fam + '|' + lado, []).append([fam, lado, dire, lin, round(cu, 3), round(pc, 3), round(score, 3), sum(ca) + sum(cb), len(ca) + len(cb),
                                                  sum(ca5) + sum(cb5), len(ca5) + len(cb5), int(min(a + b)) if a + b else None,
                                                  int(max(a + b)) if a + b else None, int(completa),
                                                  round(sum(a + b) / len(a + b), 1) if a + b else None])
    out = []
    for xs in filas.values():
        out += sorted(xs, key=lambda z: (-z[6], -z[5]))[:POR_LADO]
    return sorted(out, key=lambda z: (-z[6], -z[5])) or None
