#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v379 — LOS DOS CANALES DE TELEGRAM DE SHARPICKS: GRATIS Y VIP.

El usuario: «quiero tener grupos de Telegram… dos modelos diferentes, uno
gratis y otro como el No Win, No Pay». Este script, detrás de cada pasada del
sitio (`sitio_web.yml`), manda a cada canal sólo lo NUEVO:

  · VIP (TELEGRAM_CHAT_VIP): los picks 💎 Diamante y 🔷 Platino en cuanto
    salen (de las próximas 18 h), agrupados por partido, y su resultado.
  · GRATIS (TELEGRAM_CHAT_GRATIS): POCO Y BUENO. El usuario, al ver el primer
    envío (70 picks de golpe): «siento que es mucho… no se entiende… en el
    gratis hay que dar combinadas con alta probabilidad, máximo 1,5, o una
    individual cada cierto tiempo». Tres horarios al día (9, 14 y 19 h de
    CDMX), UNA publicación en cada uno, alternando:
      🔗 la COMBINADA del día: 2 picks de partidos distintos, cuota total
         1,30-1,50, la de mayor probabilidad de acierto;
      🎯 el PICK del día: la sencilla más segura de las próximas horas;
    su resultado al terminar, y una vez al día «Ayer en el VIP: ✅ ❌».

Qué es VIP lo dice `TELEGRAM_VIP_NIVELES` (por defecto «Diamante,Platino»).
Para no repetir, lo enviado se apunta en Supabase (`telegram_enviados`, con la
clave de servicio). Sin el canal o sin la base, no manda nada: nunca falla.

v400 — AVISOS AL MOMENTO (el usuario: «el Telegram VIP no tiene ningún valor
añadido a comparación de la suscripción… que empiece a mandar notificaciones
en ambas, en el VIP más y mejores»). La app se CONSULTA; Telegram AVISA:
  VIP
    💰 errores de cuota en cuanto aparecen (una casa que paga de más suele
       corregir pronto: el que se entera tarde ya no la alcanza);
    ⏰ «ya es hora de apostar»: cada 💎/🔷 al abrir su ventana de 4 h antes del
       partido (v351-v352: fijar ahí acierta 82 % contra 79 % al pitido);
    ♻️ si retiramos o cambiamos algo que ya mandamos;
    🌙 resumen de la noche: verdes y rojas del día.
  GRATIS
    lo de siempre (3 publicaciones, error de muestra, «ayer en el VIP») y además
    ♻️ si se retira lo publicado, 🌙 el resumen de la noche y 🎉 al llegar a
    100 miembros, 5 códigos de VIP de regalo (una sola vez).

Ejecutar:  python telegram_canales.py [--seco]
"""
import datetime as dt
import html
import json
import logging
import os
import sys
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger('telegram_canales')
DATOS = os.environ.get('WEB_DATOS', os.path.join('web', 'datos', 'hoy.json'))
PRIVADO = os.environ.get('WEB_PRIVADO', os.path.join('datos_privados', 'premium.json'))
SITIO = os.environ.get('SITIO_URL', 'https://sharpicksapp.com')
VIP_URL = os.environ.get('TELEGRAM_VIP_URL', 'https://t.me/+qqtEBbAClQwxYzYx')
HORAS_ANTES = 18
ICONO = {'Diamante': '💎', 'Platino': '🔷', 'Oro': '🥇', 'Plata': '🥈', 'Cuota alta': '💰'}
MAX_LEN = 3800
CDMX = dt.timezone(dt.timedelta(hours=-6))
# el canal gratis: horarios (hora de CDMX) y qué toca en cada uno
HORARIOS_GRATIS = ((9, 'combinada'), (14, 'pick'), (19, 'combinada'))
VENTANA_GRATIS_H = 8              # sólo partidos que empiezan en las próximas 8 h
COMB_MIN, COMB_MAX = 1.30, 1.50   # cuota total de la combinada (pedido del usuario)
PROB_MIN_GRATIS = 0.78            # cada pata (y la sencilla) con al menos esto medido
# v526 — el usuario: «más amigables y vendedores, más emojis, más visuales, breves pero impactantes, y no enviar
# mucha basura». Cada envío corto, con su emoji de deporte y, en los picks, un ticket en imagen (tarjeta_tg.py).
PIE = '\n\n🔞 <i>Juega con responsabilidad</i>'
DEP_EMO = {'Fútbol': '⚽', 'Tenis': '🎾', 'NBA': '🏀', 'NFL': '🏈', 'NHL': '🏒', 'MLB': '⚾', 'KBO': '⚾', 'Béisbol': '⚾'}
MAX_VIP_MSG = 6                   # VIP: lo mejor, no la lista entera (el resto, en la app)
VENTANA_APUESTA_H = 4             # v351: la hora para apostar
HORA_NOCHE = 22                   # 🌙 resumen del día (hora de CDMX)
META_MIEMBROS = int(os.environ.get('TG_META_MIEMBROS', '100'))
META_CODIGOS = 5
META_DIAS = int(os.environ.get('TG_META_DIAS', '7'))
# lo ya mandado con su texto (para poder avisar si se retira): {(pick, canal): fila}
_DETALLES: Dict[Tuple[str, str], Dict] = {}


def nivel(p: Dict) -> str:
    """El mismo nivel que la página (`web/app.js`, `nivel`)."""
    if p.get('tipo') == 'error':
        return 'Cuota alta'
    if p.get('elige'):
        return 'Diamante'
    pr = float(p.get('prob') or 0)
    return 'Platino' if pr >= 0.85 else ('Oro' if pr >= 0.80 else 'Plata')


def niveles_vip() -> Set[str]:
    v = os.environ.get('TELEGRAM_VIP_NIVELES') or 'Diamante,Platino,Cuota alta'   # vacío = lo de siempre
    return {x.strip().capitalize() for x in v.split(',') if x.strip()}


def _utc(s) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(str(s).replace(' ', 'T')[:19]).replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def _cuando(p: Dict, ahora: dt.datetime) -> str:
    """«hoy 21:00», «mañana 09:30» o «18/10 13:00» (hora de CDMX)."""
    d = _utc(p.get('inicio'))
    if d is None:
        return ''
    loc, hoy = d.astimezone(CDMX), ahora.astimezone(CDMX).date()
    dias = (loc.date() - hoy).days
    pre = 'hoy' if dias == 0 else ('mañana' if dias == 1 else loc.strftime('%d/%m'))
    return '%s %s' % (pre, loc.strftime('%H:%M'))


# ---------- lo ya enviado (Supabase) ----------
def _sb():
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    return url.rstrip('/') + '/rest/v1/telegram_enviados', {
        'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}


def ya_enviados() -> Optional[Set[Tuple[str, str, str]]]:
    """(pick, canal, tipo) ya mandados; None si no hay base (no se manda nada)."""
    sb = _sb()
    if sb is None:
        return None
    import requests
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=4)).isoformat()
    r = requests.get(sb[0], headers=sb[1], timeout=30,
                     params={'select': '*', 'enviado': 'gte.' + desde, 'limit': 20000})
    if not r.ok:
        logger.warning('[telegram] no se pudo leer lo enviado: %s', r.status_code)
        return None
    _DETALLES.clear()
    for x in r.json():
        if x.get('tipo') == 'pick' and x.get('texto'):
            _DETALLES[(x['pick'], x['canal'])] = x
    return {(x['pick'], x['canal'], x['tipo']) for x in r.json()}


def apuntar(filas: List[Tuple]) -> None:
    """(pick, canal, tipo) o, para los picks, (pick, canal, tipo, texto,
    partido, inicio): con el texto se puede avisar si luego se retira."""
    sb = _sb()
    if sb is None or not filas:
        return
    import requests
    h = dict(sb[1], Prefer='resolution=ignore-duplicates,return=minimal')
    filas = [tuple(f) + (None,) * (6 - len(f)) for f in filas]
    requests.post(sb[0], headers=h, timeout=30,
                  json=[{'pick': a, 'canal': b, 'tipo': c, 'texto': d, 'partido': e, 'inicio': f}
                        for a, b, c, d, e, f in filas])


def _cubre_pick(p: Dict, canal: str) -> Tuple:
    return (p['id'], canal, 'pick', p.get('apuesta'), p.get('partido'), p.get('inicio'))


# ---------- formato ----------
def _e(x) -> str:
    return html.escape(str(x if x is not None else ''))


def _apuesta(p: Dict) -> str:
    if p.get('tipo') == 'error':
        return '🚨 <b>%s</b> · 💸 %.2f · 🎯 %d %% · +%d %% de valor%s' % (
            _e(p.get('apuesta')), float(p.get('cuota') or 0), round(100 * float(p.get('prob') or 0)),
            round(100 * float(p.get('ventaja') or 0)), (' en ' + _e(p.get('casa'))) if p.get('casa') else '')
    return '✅ <b>%s</b> · 💸 %.2f · 🎯 %d %%' % (
        _e(p.get('apuesta')), float(p.get('cuota') or 0), round(100 * float(p.get('prob') or 0)))


def _ticket(titulo: str, ps: List[Dict], ahora: dt.datetime, etiqueta: str) -> Optional[bytes]:
    """v526 — el ticket en imagen (si algo falla, el mensaje sale sólo con texto)."""
    try:
        import tarjeta_tg
        return tarjeta_tg.ticket(titulo, [{'partido': p.get('partido'), 'apuesta': p.get('apuesta'), 'cuota': p.get('cuota'),
                                            'prob': p.get('prob'), 'cuando': _cuando(p, ahora).upper()} for p in ps], etiqueta)
    except Exception as e:
        logger.warning('[telegram] sin ticket: %s', e)
        return None


def _cab_partido(p: Dict, ahora: dt.datetime, icono: str = '') -> str:
    return '%s %s<b>%s</b> · 🕒 %s' % (DEP_EMO.get(p.get('deporte'), '🎯'), icono + ' ' if icono else '', _e(p.get('partido')), _cuando(p, ahora))


def _por_partido(ps: List[Dict], ahora: dt.datetime) -> List[str]:
    """Un bloque por partido con sus apuestas debajo (nunca el partido dos veces)."""
    g: Dict[str, List[Dict]] = {}
    for p in sorted(ps, key=lambda x: (str(x.get('inicio')), not x.get('elige'), -float(x.get('prob') or 0))):
        g.setdefault('%s|%s' % (p.get('partido'), str(p.get('inicio'))[:10]), []).append(p)
    out = []
    for grupo in g.values():
        mejor = max(grupo, key=lambda x: (bool(x.get('elige')), float(x.get('prob') or 0)))
        out.append(_cab_partido(grupo[0], ahora, ICONO[nivel(mejor)]) + '\n' +
                   '\n'.join(_apuesta(p) for p in grupo))
    return out


def _trozos(cab: str, bloques: List[str], pie: str = PIE, sep: str = '\n\n') -> List[str]:
    out, actual = [], cab
    for b in bloques:
        if len(actual) + len(b) + len(pie) + 2 > MAX_LEN:
            out.append(actual + pie)
            actual = cab + ' (sigue)'
        actual += sep + b
    out.append(actual + pie)
    return out


def _resultado_txt(ps: List[Dict]) -> Optional[str]:
    """'verde' / 'roja' cuando ya se sabe; None mientras falte alguna."""
    est = [p.get('estado') for p in ps]
    if any(e == 'roja' for e in est):
        return 'roja'
    if all(e in ('verde', 'nula') for e in est) and any(e == 'verde' for e in est):
        return 'verde'
    return None


# ---------- el canal VIP ----------
def _retirados(picks: List[Dict], enviados: Set, canal: str, ahora: dt.datetime) -> List[Dict]:
    """Lo que ya mandamos a `canal`, aún sin empezar, que el modelo ya NO da.
    Sólo con una pasada completa (si viniera casi vacía por un fallo, se callaría)."""
    pend = [p for p in picks if p.get('estado') == 'pendiente']
    if len(pend) < 30:
        return []
    vivos = {p['id'] for p in picks}
    out = []
    for (k, c), x in list(_DETALLES.items()):
        ini = _utc(x.get('inicio'))
        if c != canal or ini is None or ini <= ahora or (k, canal, 'retirado') in enviados:
            continue
        ids = k[5:].split('+') if k.startswith('comb:') else [k]
        if any(i not in vivos for i in ids):
            out.append(x)
    return out


def _avisos_retiro(picks: List[Dict], enviados: Set, canal: str, ahora: dt.datetime) -> List[Tuple[str, List]]:
    rs = _retirados(picks, enviados, canal, ahora)
    if not rs:
        return []
    t = ('♻️ <b>Cambio</b>: ya no recomendamos esto (el modelo lo retiró con los datos nuevos):\n\n' +
         '\n'.join('✖️ %s · %s' % (_e(x.get('texto')), _e(x.get('partido'))) for x in rs) +
         '\n\nSi ya lo metiste, tú decides; nosotros ya no lo contamos.' + PIE)
    return [(t, [(x['pick'], canal, 'retirado') for x in rs])]


def _dia_cdmx(p: Dict) -> Optional[str]:
    ini = _utc(p.get('inicio'))
    return ini.astimezone(CDMX).strftime('%Y-%m-%d') if ini else None


def _tres(enviados) -> Set:
    """(pick, canal, tipo) aunque llegue con el texto detrás (v400)."""
    return {tuple(x[:3]) for x in enviados}


def armar_vip(picks: List[Dict], enviados: Set, ahora: dt.datetime) -> List[Tuple[str, List]]:
    enviados = _tres(enviados)
    vip = niveles_vip()
    out = []
    loc = ahora.astimezone(CDMX)
    pend = [p for p in picks if nivel(p) in vip and p.get('estado') == 'pendiente'
            and _utc(p.get('inicio')) is not None and _utc(p.get('inicio')) > ahora
            and (p['id'], 'vip', 'pick') not in enviados]
    # 💰 errores de cuota: AL MOMENTO (se corrigen pronto)
    errs = [p for p in pend if p.get('tipo') == 'error'
            and _utc(p.get('inicio')) <= ahora + dt.timedelta(hours=HORAS_ANTES)]
    if errs:
        trozos = _trozos('🚨💰 <b>Error de cuota · al momento</b>\n¡Corre! Las casas lo corrigen rápido. Apuesta poquito 👇',
                         _por_partido(errs, ahora))
        out += [(t, []) for t in trozos[:-1]] + [(trozos[-1], [_cubre_pick(p, 'vip') for p in errs])]
    # ⏰ los demás, al abrir su ventana para apostar (4 h antes)
    ya = [p for p in pend if p.get('tipo') != 'error'
          and _utc(p.get('inicio')) <= ahora + dt.timedelta(hours=VENTANA_APUESTA_H)]
    if ya:
        # lo mejor primero (💎 y la probabilidad más alta); el resto, en la app
        top = sorted(ya, key=lambda p: (not p.get('elige'), -float(p.get('prob') or 0)))[:MAX_VIP_MSG]
        mas = len(ya) - len(top)
        t = ('💎🔥 <b>VIP · Ya es hora de apostar</b> ⏰\n\n' + '\n\n'.join(_por_partido(top, ahora)) +
             ('\n\n➕ <b>%d más</b> en la app 👉 %s' % (mas, SITIO) if mas > 0 else '') + PIE)
        out.append((t, [_cubre_pick(p, 'vip') for p in ya], _ticket('Picks VIP · hora de apostar', top, ahora, 'VIP')))
    out += _avisos_retiro(picks, enviados, 'vip', ahora)
    res = [p for p in picks if nivel(p) in vip and p.get('estado') in ('verde', 'roja')
           and _utc(p.get('inicio')) is not None and _utc(p.get('inicio')) >= ahora - dt.timedelta(hours=8)
           and (p['id'], 'vip', 'resultado') not in enviados]
    if res:
        v = sum(1 for p in res if p.get('estado') == 'verde')
        # breve: el marcador del lote y sólo las verdes (las rojas cuentan arriba y están en el historial)
        verdes = [p for p in res if p.get('estado') == 'verde'][:5]
        t = ('📊 <b>Resultados VIP</b> · ✅ %d ❌ %d%s\n' % (v, len(res) - v, ' 🔥' if v >= 0.8 * len(res) else '') +
             '\n'.join('✅ %s · %s %s' % (_e(p.get('apuesta')), _e(p.get('partido')), _e(p.get('marcador') or '')) for p in verdes) +
             ('\n…y %d verdes más' % (v - len(verdes)) if v > len(verdes) else '') + '\n\n📈 Todo, verde y rojo, en el historial 👉 ' + SITIO)
        out.append((t, [(p['id'], 'vip', 'resultado') for p in res]))
    # 🌙 el resumen de la noche
    hoy = loc.strftime('%Y-%m-%d')
    if loc.hour >= HORA_NOCHE and ('noche:' + hoy, 'vip', 'resumen') not in enviados:
        dia = [p for p in picks if nivel(p) in vip and _dia_cdmx(p) == hoy]
        t = _resumen_noche('💎 <b>Hoy en el VIP</b>', dia)
        if t:
            out.append((t, [('noche:' + hoy, 'vip', 'resumen')]))
    return out


def _resumen_noche(titulo: str, ps: List[Dict]) -> Optional[str]:
    hechos = [p for p in ps if p.get('estado') in ('verde', 'roja')]
    if not hechos:
        return None
    v = sum(1 for p in hechos if p.get('estado') == 'verde')
    er = [p for p in hechos if p.get('tipo') == 'error']
    ev = sum(1 for p in er if p.get('estado') == 'verde')
    falta = sum(1 for p in ps if p.get('estado') in ('pendiente', 'vivo'))
    return ('🌙 %s: ✅ %d ❌ %d · %d %%' % (titulo, v, len(hechos) - v, round(100 * v / len(hechos))) +
            (('\n💰 Errores de cuota: ✅ %d ❌ %d' % (ev, len(er) - ev)) if er else '') +
            (('\n⏳ %d por terminar' % falta) if falta else '') +
            '\n\nTodo, verde y rojo, en el historial: %s' % SITIO)


# ---------- el canal gratis: poco y bueno ----------
def candidatas_gratis(picks: List[Dict], ahora: dt.datetime) -> List[Dict]:
    """v381 — sin los niveles del VIP (💎/🔷): si el gratis los diera, el VIP
    no tendría nada propio. Tampoco nada premium (su texto no es público)."""
    fin = ahora + dt.timedelta(hours=VENTANA_GRATIS_H)
    vip = niveles_vip()
    out = []
    for p in picks:
        ini = _utc(p.get('inicio'))
        if (p.get('estado') == 'pendiente' and p.get('cuota') and ini is not None
                and nivel(p) not in vip and not p.get('premium')
                and float(p.get('prob') or 0) >= PROB_MIN_GRATIS
                and ahora + dt.timedelta(minutes=20) < ini <= fin):
            out.append(p)
    return out


def mejor_combinada(cands: List[Dict]) -> Optional[List[Dict]]:
    """2 picks de partidos distintos, cuota total 1,30-1,50, máxima probabilidad
    conjunta (producto de lo medido: las patas de partidos distintos son
    independientes)."""
    mejor, pm = None, 0.0
    for a, b in combinations(cands, 2):
        if a.get('partido') == b.get('partido'):
            continue
        c = float(a['cuota']) * float(b['cuota'])
        if not (COMB_MIN <= c <= COMB_MAX):
            continue
        pj = float(a['prob']) * float(b['prob'])
        if pj > pm:
            mejor, pm = sorted([a, b], key=lambda x: str(x.get('inicio'))), pj
    return mejor


def mejor_sencilla(cands: List[Dict]) -> Optional[Dict]:
    """La más segura que pague algo (cuota ≥ 1,20); si no hay, la más segura."""
    con = [p for p in cands if float(p['cuota']) >= 1.20] or cands
    return max(con, key=lambda p: (float(p['prob']), float(p['cuota'])), default=None)


def armar_gratis(picks: List[Dict], enviados: Set, ahora: dt.datetime) -> List[Tuple[str, List]]:
    enviados = _tres(enviados)
    out = []
    loc = ahora.astimezone(CDMX)
    hoy = loc.strftime('%Y-%m-%d')
    toca = [(h, t) for h, t in HORARIOS_GRATIS if loc.hour >= h]
    if toca:
        h, tipo = toca[-1]
        clave = 'horario:%s:%02d' % (hoy, h)
        if (clave, 'gratis', 'horario') not in enviados:
            cands = candidatas_gratis(picks, ahora)
            comb = mejor_combinada(cands) if tipo == 'combinada' else None
            sen = None if comb else mejor_sencilla(cands)
            if comb:
                c = float(comb[0]['cuota']) * float(comb[1]['cuota'])
                pj = float(comb[0]['prob']) * float(comb[1]['prob'])
                t = ('🔗🔥 <b>Combinada del día</b> · cuota total <b>%.2f</b> · 🎯 ~%d %%\n\n' % (c, round(100 * pj)) +
                     '\n\n'.join(_cab_partido(p, ahora) + '\n' + _apuesta(p) for p in comb) +
                     '\n\n💎 ¿Quieres más? En el VIP hay picks todo el día 👉 ' + SITIO + PIE)
                out.append((t, [(clave, 'gratis', 'horario'),
                                ('comb:' + '+'.join(p['id'] for p in comb), 'gratis', 'pick',
                                 ' + '.join(str(p.get('apuesta')) for p in comb),
                                 ' / '.join(str(p.get('partido')) for p in comb), comb[0].get('inicio'))],
                            _ticket('Combinada del día', comb, ahora, 'GRATIS')))
            elif sen:
                t = ('🎯🆓 <b>Pick del día</b>\n\n' + _cab_partido(sen, ahora) + '\n' + _apuesta(sen) +
                     '\n\n💎 En el VIP hay más todos los días 👉 ' + SITIO + PIE)
                out.append((t, [(clave, 'gratis', 'horario'), _cubre_pick(sen, 'gratis')], _ticket('Pick del día', [sen], ahora, 'GRATIS')))
            else:
                out.append(('', [(clave, 'gratis', 'horario')]))     # nada que valga: no se publica
    # el resultado de lo que se publicó
    por_id = {p['id']: p for p in picks}
    for (k, canal, tipo) in sorted(enviados):
        if canal != 'gratis' or tipo != 'pick' or (k, 'gratis', 'resultado') in enviados:
            continue
        ps = [por_id.get(i) for i in (k[5:].split('+') if k.startswith('comb:') else [k])]
        if not all(ps):
            continue
        r = _resultado_txt(ps)
        if r is None:
            continue
        que = 'Combinada' if len(ps) > 1 else 'Pick'
        t = ('%s <b>%s %s</b>%s\n' % ('✅' if r == 'verde' else '❌', que, 'cumplida' if r == 'verde' else 'fallada',
                                      ' 🎉💰' if r == 'verde' else '') +
             '\n'.join('%s %s · %s %s' % ('✅' if p.get('estado') == 'verde' else ('❌' if p.get('estado') == 'roja' else '➖'),
                                          _e(p.get('apuesta')), _e(p.get('partido')), _e(p.get('marcador') or ''))
                       for p in ps) + PIE)
        out.append((t, [(k, 'gratis', 'resultado')]))
    # v384 — a mediodía, los 1-2 errores de cuota «muestra» (los más probables)
    if loc.hour >= 12:
        clave = 'error-gratis:' + hoy
        mues = [p for p in picks if p.get('tipo') == 'error' and p.get('gratis') and p.get('estado') == 'pendiente'
                and (p['id'], 'gratis', 'pick') not in enviados]
        if mues and (clave, 'gratis', 'horario') not in enviados:
            t = ('🚨💰 <b>Error de cuota del día</b>\nUna casa paga de más. Apuesta poquito 👇\n\n' +
                 '\n\n'.join(_cab_partido(p, ahora) + '\n' + _apuesta(p) for p in mues) +
                 '\n\n🔒 En el VIP llegan al momento, todos los días 👉 ' + SITIO + PIE)
            out.append((t, [(clave, 'gratis', 'horario')] + [(p['id'], 'gratis', 'pick') for p in mues]))
    # una vez al día: cómo le fue ayer al VIP (la prueba de que vale la pena)
    ayer = (loc - dt.timedelta(days=1)).strftime('%Y-%m-%d')
    clave = 'resumen-vip:' + ayer
    if loc.hour >= 9 and (clave, 'gratis', 'resumen') not in enviados:
        vip = niveles_vip()
        ps = [p for p in picks if nivel(p) in vip and p.get('estado') in ('verde', 'roja')
              and _utc(p.get('inicio')) is not None
              and _utc(p.get('inicio')).astimezone(CDMX).strftime('%Y-%m-%d') == ayer]
        if ps:
            v = sum(1 for p in ps if p.get('estado') == 'verde')
            # v383 — el enlace del VIP ya no se publica: se da en la app a quien le toca
            t = ('💎 <b>Ayer en el VIP</b>: ✅ %d ❌ %d · <b>%d %%</b> 🔥\n'
                 '👉 Hazte VIP y recíbelos al momento: %s' % (v, len(ps) - v, round(100 * v / len(ps)), SITIO))
            out.append((t, [(clave, 'gratis', 'resumen')]))
    out += _avisos_retiro(picks, enviados, 'gratis', ahora)
    # 🌙 la noche: lo que se publicó aquí y el total del día en la app
    if loc.hour >= HORA_NOCHE and ('noche:' + hoy, 'gratis', 'resumen') not in enviados:
        dia = [p for p in picks if _dia_cdmx(p) == hoy and p.get('tipo') != 'error']
        t = _resumen_noche('<b>Hoy en SharPicks</b> (todos los picks de la app)', dia)
        if t:
            out.append((t, [('noche:' + hoy, 'gratis', 'resumen')]))
    return out


def meta_miembros(chat: str, enviados: Set) -> Optional[Tuple[str, List]]:
    """🎉 Al llegar a META_MIEMBROS en el canal gratis, UNA vez: 5 códigos de
    VIP de META_DIAS días, creados en la base (`codigos_regalo`)."""
    clave = 'meta-miembros:%d' % META_MIEMBROS
    if not chat or (clave, 'gratis', 'regalo') in enviados:
        return None
    import bot_telegram as bt
    r, _ = bt._post('getChatMemberCount', timeout=20, json={'chat_id': chat})
    try:
        n = int(r.json().get('result')) if r is not None and r.ok else 0
    except Exception:
        n = 0
    if n < META_MIEMBROS:
        return None
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    import requests
    import secrets
    abc = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    cods = ['SHARP-%s-%s' % (''.join(secrets.choice(abc) for _ in range(4)), ''.join(secrets.choice(abc) for _ in range(4)))
            for _ in range(META_CODIGOS)]
    rr = requests.post(url.rstrip('/') + '/rest/v1/codigos_regalo', timeout=30,
                       headers={'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                                'Prefer': 'return=minimal'},
                       json=[{'codigo': c, 'dias': META_DIAS} for c in cods])
    if not rr.ok:
        logger.warning('[telegram] no se pudieron crear los códigos: %s %s', rr.status_code, rr.text[:200])
        return None
    t = ('🎉 <b>¡Ya somos %d en la comunidad!</b>\nPara celebrarlo regalamos <b>%d códigos de %d días de VIP</b>. '
         'El primero que canjee cada uno se lo queda: entra a %s → Mi cuenta → 🎁 Canjear código.\n\n%s' %
         (n, META_CODIGOS, META_DIAS, SITIO, '\n'.join('<code>%s</code>' % c for c in cods)) + PIE)
    return t, [(clave, 'gratis', 'regalo')]


# ---------- v527 — avisos personales: los picks de SUS deportes o de SU partido, por mensaje directo ----------
DEP_ALERTA = {'MLB': 'Béisbol', 'KBO': 'Béisbol'}


def clave_partido(p: Dict) -> str:
    """La misma clave que la página (`clavePartido`) y que las alertas por partido."""
    L, _, V = str(p.get('partido') or '').partition(' vs ')
    return '|'.join([p.get('deporte') or '', ' / '.join(sorted([L.lower().strip(), V.lower().strip()])), _dia_cdmx(p) or str(p.get('fecha') or '')])


def armar_personales(picks: List[Dict], destinos: List[Dict], ya: Set[str], ahora: dt.datetime,
                     abiertos: Optional[Dict[str, Set[str]]] = None, con_cuenta: bool = False) -> List[Tuple]:
    """[(chat, texto, cubre)]: a cada quien, en UN mensaje, sus picks que ya están en hora de apostar. El VIP los ve
    completos; los demás, completos sólo los que no son VIP ni de pago (los otros, con candado para desbloquear)."""
    vip_niv = niveles_vip()
    ventana = [p for p in picks if p.get('estado') == 'pendiente' and _utc(p.get('inicio')) is not None
               and ahora + dt.timedelta(minutes=10) < _utc(p.get('inicio')) <= ahora + dt.timedelta(hours=VENTANA_APUESTA_H)]
    usuarios: Dict[str, Dict] = {}
    for d in destinos:
        u = usuarios.setdefault(d['usuario'], {'chat': d['chat'], 'vip': bool(d.get('vip')), 'dep': set(), 'par': set()})
        if d['tipo'] == 'deporte':
            u['dep'].add(d['valor'])
        elif d['tipo'] == 'partido':
            u['par'].add(d['valor'])
    out = []
    for uid, u in usuarios.items():
        suyos = [p for p in ventana if (DEP_ALERTA.get(p.get('deporte'), p.get('deporte')) in u['dep'] or clave_partido(p) in u['par'])
                 and 'dm:%s:%s' % (uid, p['id']) not in ya]
        if not suyos:
            continue
        suyos.sort(key=lambda p: (not p.get('elige'), -float(p.get('prob') or 0)))
        top = suyos[:MAX_VIP_MSG]
        lineas = []
        for p in top:
            # v534 — completo: al VIP, a lo que no es de pago, a lo que ESA persona desbloqueó con monedas, y a todos
            # con cuenta si el ajuste «premium_con_cuenta» está prendido (la misma regla que la página)
            if u['vip'] or con_cuenta or p['id'] in (abiertos or {}).get(uid, set()) or not (p.get('premium') or nivel(p) in vip_niv):
                lineas.append(_cab_partido(p, ahora, ICONO.get(nivel(p), '')) + '\n' + _apuesta(p))
            else:
                lineas.append(_cab_partido(p, ahora, ICONO.get(nivel(p), '')) + '\n🔒 <b>Pick %s</b> · desbloquéalo en la app' % _e(nivel(p)))
        mas = len(suyos) - len(top)
        t = ('🔔 <b>Tus picks</b> · ⏰ ya es hora de apostar\n\n' + '\n\n'.join(lineas) +
             ('\n\n➕ %d más en la app' % mas if mas > 0 else '') + '\n\n👉 ' + SITIO + PIE)
        out.append((u['chat'], t, [('dm:%s:%s' % (uid, p['id']), 'dm', 'pick') for p in suyos]))
    return out


def armar_mis_cosas(picks: List[Dict], ligados: List[Dict], seguidos: List[Dict], combs: List[Dict], ya: Set[str]) -> List[Tuple]:
    """v530 — el usuario: «si estoy siguiendo un partido, quiero que se mande notificación sobre eso o sobre la
    combinada que metí». A cada quien que ligó su Telegram: el resultado de los picks que sigue (☆ Seguir) y de sus
    combinadas, en cuanto se deciden. [(chat, texto, cubre)], un mensaje por persona."""
    por_id = {p['id']: p for p in picks}
    chats = {x['usuario']: x['chat'] for x in ligados}
    out = []
    for uid, chat in chats.items():
        lineas, cubre = [], []
        for s in seguidos:
            p = por_id.get(s.get('pick'))
            k = 'dm-seg:%s:%s' % (uid, s.get('pick'))
            if s.get('usuario') != uid or not p or p.get('estado') not in ('verde', 'roja') or k in ya:
                continue
            ok = p['estado'] == 'verde'
            lineas.append('%s <b>%s</b> · %s %s' % ('✅' if ok else '❌', _e(p.get('apuesta')), _e(p.get('partido')), _e(p.get('marcador') or '')))
            cubre.append((k, 'dm', 'resultado'))
        for c in combs:
            k = 'dm-comb:%s:%s' % (uid, c.get('id'))
            if c.get('usuario') != uid or c.get('estado') not in ('verde', 'roja') or k in ya:
                continue
            ok = c['estado'] == 'verde'
            lineas.append(('🎉 <b>¡Tu combinada se cumplió!</b> · cuota %.2f%s' % (float(c.get('cuota') or 0),
                           (' · +%s 🪙' % c['premio']) if c.get('premio') else '')) if ok else
                          '❌ Tu combinada de cuota %.2f no salió' % float(c.get('cuota') or 0))
            cubre.append((k, 'dm', 'resultado'))
        if lineas:
            n_ok = sum(1 for l in lineas if l.startswith(('✅', '🎉')))
            t = ('🔔 <b>Lo tuyo</b>%s\n\n' % (' 🔥' if n_ok == len(lineas) else '') + '\n'.join(lineas) + '\n\n👉 ' + SITIO)
            out.append((chat, t, cubre))
    return out


def mis_cosas() -> Optional[Tuple[List[Dict], List[Dict], List[Dict], Set[str]]]:
    """(ligados, seguidos, combinadas de usuario, lo ya avisado), con la llave de servicio."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    import requests
    b, h = url.rstrip('/') + '/rest/v1/', {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
    r = requests.post(b + 'rpc/telegram_ligados', headers=h, json={}, timeout=30)
    if not r.ok or not r.json():
        return None
    ligados = r.json()
    ids = ','.join(x['usuario'] for x in ligados)
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).isoformat()
    seg = requests.get(b + 'seguidos', headers=h, timeout=30, params={'select': 'usuario,pick', 'usuario': 'in.(%s)' % ids, 'limit': 5000})
    com = requests.get(b + 'combinadas_usuario', headers=h, timeout=30,
                       params={'select': 'id,usuario,cuota,estado,premio', 'usuario': 'in.(%s)' % ids, 'estado': 'in.(verde,roja)',
                               'creado': 'gte.' + desde, 'limit': 5000})
    e = requests.get(b + 'telegram_enviados', headers=h, timeout=30,
                     params={'select': 'pick', 'canal': 'eq.dm', 'tipo': 'eq.resultado', 'enviado': 'gte.' + desde, 'limit': 20000})
    return ligados, (seg.json() if seg.ok else []), (com.json() if com.ok else []), {x['pick'] for x in (e.json() if e.ok else [])}


def destinos_alertas() -> Optional[Tuple[List[Dict], Set[str]]]:
    """(quién quiere qué, lo ya mandado por mensaje directo), con la llave de servicio."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    import requests
    h = {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
    r = requests.post(url.rstrip('/') + '/rest/v1/rpc/alertas_destinos', headers=h, json={}, timeout=30)
    if not r.ok:
        return None
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat()
    e = requests.get(url.rstrip('/') + '/rest/v1/telegram_enviados', headers=h, timeout=30,
                     params={'select': 'pick', 'canal': 'eq.dm', 'tipo': 'eq.pick', 'enviado': 'gte.' + desde, 'limit': 20000})
    return r.json(), {x['pick'] for x in (e.json() if e.ok else [])}


def desbloqueos_de(usuarios: List[str]) -> Tuple[Dict[str, Set[str]], bool]:
    """v534 — lo que cada quien desbloqueó con monedas, y si el lanzamiento abre lo premium a toda cuenta."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key or not usuarios:
        return {}, False
    import requests
    b, h = url.rstrip('/') + '/rest/v1/', {'apikey': key, 'Authorization': 'Bearer ' + key}
    out: Dict[str, Set[str]] = {}
    r = requests.get(b + 'desbloqueos', headers=h, timeout=30, params={'select': 'usuario,pick', 'usuario': 'in.(%s)' % ','.join(usuarios), 'limit': 20000})
    for x in (r.json() if r.ok else []):
        out.setdefault(x['usuario'], set()).add(x['pick'])
    a = requests.get(b + 'ajustes', headers=h, timeout=30, params={'select': 'valor', 'clave': 'eq.premium_con_cuenta'})
    return out, bool(a.ok and a.json() and str(a.json()[0].get('valor')) == '1')


def revisar_vip(chat_vip: Optional[str]) -> int:
    """v534 — a quien se le acabó el VIP: fuera del grupo VIP (sacar = banear y desbanear, así puede volver si renueva),
    y un aviso. Desde ese momento sus avisos personales ya le llegan como a cualquier cuenta gratis."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key or not chat_vip:
        return 0
    import requests
    import bot_telegram as bt
    b, h = url.rstrip('/') + '/rest/v1/', {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
    r = requests.post(b + 'rpc/telegram_vip_vencidos', headers=h, json={}, timeout=30)
    fuera = list(r.json() if r.ok else [])
    # v536 — EL BARRIDO de cada pasada: Telegram no deja a ningún bot listar a los miembros de un grupo, así que se revisa
    # a cada quien que ligó su Telegram en la app: si está en el grupo VIP sin VIP vigente, sale; si es VIP, queda
    # anotado (para sacarlo el día que se le acabe). Los que entraron con el enlace viejo sin ligarse no se pueden ver.
    l = requests.post(b + 'rpc/telegram_ligados', headers=h, json={}, timeout=30)
    pv = requests.get(b + 'privados', headers=h, params={'select': 'valor', 'clave': 'eq.telegram_vip'}, timeout=30)
    enlace = (pv.json()[0].get('valor') if pv.ok and pv.json() else None)
    invitar: List[Dict] = []
    vistos = {x['chat'] for x in fuera}
    for x in (l.json() if l.ok else [])[:500]:
        if x['chat'] in vistos:
            continue
        m, _ = bt._post('getChatMember', timeout=20, json={'chat_id': chat_vip, 'user_id': x['chat']})
        est = ((m.json().get('result') or {}).get('status') if m is not None and m.ok else None)
        if est not in ('member', 'restricted', 'administrator', 'creator'):
            # v536 — VIP ligado que aún no está en el grupo: se le manda el enlace UNA vez por suscripción
            if x.get('vip') and enlace and est in ('left', 'kicked', None):
                invitar.append(x)
            continue
        if est in ('administrator', 'creator'):
            continue
        if x.get('vip'):
            requests.patch(b + 'telegram_usuarios', headers=dict(h, Prefer='return=minimal'), params={'usuario': 'eq.' + x['usuario']},
                           json={'en_vip': True}, timeout=30)
        else:
            fuera.append(x)
    # el enlace a quien ya es VIP y no ha entrado (una vez por suscripción: la clave lleva su fecha de vencimiento)
    if invitar:
        ids = ','.join(x['usuario'] for x in invitar)
        pf = requests.get(b + 'perfiles', headers=h, params={'select': 'id,plan_hasta', 'id': 'in.(%s)' % ids}, timeout=30)
        hasta = {p['id']: str(p.get('plan_hasta') or 'sin-fin')[:10] for p in (pf.json() if pf.ok else [])}
        ya = requests.get(b + 'telegram_enviados', headers=h, timeout=30,
                          params={'select': 'pick', 'canal': 'eq.dm', 'tipo': 'eq.vip-enlace', 'limit': 5000})
        ya = {y['pick'] for y in (ya.json() if ya.ok else [])}
        for x in invitar:
            k = 'vip-enlace:%s:%s' % (x['usuario'], hasta.get(x['usuario'], ''))
            if k in ya:
                continue
            if enviar_a(str(x['chat']), '💎 <b>¡Ya eres VIP en SharPicks!</b>\n\nEntra al grupo VIP aquí 👉 %s\n'
                        'Toca «Solicitar unirse»: te aprobamos al momento.' % _e(enlace)):
                apuntar([(k, 'dm', 'vip-enlace')])
    n = 0
    for x in fuera:
        ok, _ = bt._post('banChatMember', timeout=30, json={'chat_id': chat_vip, 'user_id': x['chat']})
        if ok is None or not ok.ok:
            continue
        bt._post('unbanChatMember', timeout=30, json={'chat_id': chat_vip, 'user_id': x['chat'], 'only_if_banned': True})
        requests.patch(b + 'telegram_usuarios', headers=dict(h, Prefer='return=minimal'), params={'usuario': 'eq.' + x['usuario']},
                       json={'en_vip': False}, timeout=30)
        enviar_a(str(x['chat']), '💎 Tu VIP de SharPicks terminó, por eso saliste del grupo VIP.\n\n'
                 '🔔 Te seguimos avisando con lo gratis. Para volver, renueva en ' + SITIO + ' → Planes y pide entrar otra vez: '
                 'te aprobamos al momento.')
        n += 1
    return n


def armar(picks: List[Dict], enviados: Set, ahora: Optional[dt.datetime] = None) -> Dict[str, List]:
    """{canal: [(texto, [(pick, canal, tipo) que cubre])]} con sólo lo nuevo."""
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    return {'vip': armar_vip(picks, enviados, ahora), 'gratis': armar_gratis(picks, enviados, ahora)}


def enviar_a(chat: str, texto: str, foto: Optional[bytes] = None) -> bool:
    import bot_telegram as bt
    if foto and len(texto) <= 1024:               # v526 — el ticket con el texto de pie de foto
        r, motivo = bt._post('sendPhoto', timeout=60, data={'chat_id': chat, 'caption': texto, 'parse_mode': 'HTML'},
                             files={'photo': ('sharpicks.png', foto, 'image/png')})
        if r is not None and r.ok:
            return True
        logger.warning('[telegram] sin foto (%s): va sólo el texto', motivo)
    r, motivo = bt._post('sendMessage', timeout=30, json={
        'chat_id': chat, 'text': texto, 'parse_mode': 'HTML', 'disable_web_page_preview': True})
    if r is not None and r.ok:
        return True
    logger.warning('[telegram] %s', motivo)
    return False


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    seco = '--seco' in sys.argv
    chats = {'vip': os.environ.get('TELEGRAM_CHAT_VIP'), 'gratis': os.environ.get('TELEGRAM_CHAT_GRATIS')}
    if not seco and (not os.environ.get('TELEGRAM_BOT_TOKEN') or not any(chats.values())):
        print('telegram: sin bot o sin canales (TELEGRAM_CHAT_VIP / TELEGRAM_CHAT_GRATIS): no se manda nada')
        return 0
    try:
        picks = json.load(open(DATOS, encoding='utf-8')).get('picks') or []
    except Exception as e:
        print('telegram: sin datos del sitio (%s)' % e)
        return 0
    # v381 — el texto real de lo premium (el fichero público lo lleva tapado)
    try:
        reales = json.load(open(PRIVADO, encoding='utf-8'))
        for p in picks:
            if p.get('id') in reales:
                p['apuesta'] = reales[p['id']]
    except Exception:
        pass
    enviados = set() if seco else ya_enviados()
    if enviados is None:
        print('telegram: sin la base no se sabe qué ya se mandó: no se manda nada')
        return 0
    lotes = armar(picks, enviados)
    if not seco:
        try:
            m = meta_miembros(chats.get('gratis'), enviados)
            if m:
                lotes['gratis'].append(m)
        except Exception as e:
            logger.warning('[telegram] meta de miembros: %s', e)
    for canal, msgs in lotes.items():
        for item in msgs:
            texto, cubre, foto = item[0], item[1], (item[2] if len(item) > 2 else None)
            if not texto:                      # horario sin nada que valga: sólo se apunta
                if not seco:
                    apuntar(cubre)
                continue
            if seco or not chats.get(canal):
                print('--- %s ---\n%s' % (canal, texto))
                continue
            if enviar_a(chats[canal], texto, foto):
                apuntar(cubre)
    # v527 — los avisos personales (quien ligó su Telegram en la app y eligió deportes o partidos)
    personales = 0
    try:
        dd = destinos_alertas() if not seco else None
        if dd:
            ab, con_cuenta = desbloqueos_de(sorted({d['usuario'] for d in dd[0]}))
            for chat, texto, cubre in armar_personales(picks, dd[0], dd[1], dt.datetime.now(dt.timezone.utc), ab, con_cuenta):
                if enviar_a(str(chat), texto):
                    apuntar(cubre)
                    personales += 1
        mc = mis_cosas() if not seco else None                 # v530 — sus picks seguidos y sus combinadas
        if mc:
            for chat, texto, cubre in armar_mis_cosas(picks, *mc):
                if enviar_a(str(chat), texto):
                    apuntar(cubre)
                    personales += 1
    except Exception as e:
        logger.warning('[telegram] avisos personales: %s', e)
    try:
        fuera = revisar_vip(chats.get('vip')) if not seco else 0
        if fuera:
            print('telegram: %d sin VIP vigente salieron del grupo VIP' % fuera)
    except Exception as e:
        logger.warning('[telegram] revisar el VIP: %s', e)
    print('telegram: %s · personales %d' % ({k: len([m for m in v if m[0]]) for k, v in lotes.items()}, personales))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
