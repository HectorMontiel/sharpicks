#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v520 — EL PULSO EN VIVO, DEL LADO DEL SERVIDOR: avisos y la recomendación «IA + modelo».

El usuario: «la app debe mandar notificaciones de los partidos donde hay más probabilidad de que se cumpla lo
del pulso» y «tenemos conectado a Gemini… que nos dé la mejor recomendación para meter en pulso, y esa debe
destacarse». Corre en el runner del PC (pulso_vivo.yml, una hora por corrida) y cada 2 minutos:

  1. Lee los partidos de fútbol de hoy del sitio publicado (picks y sólo análisis) que van en el 2.º tiempo
     (ESPN), y les calcula el Pulso con el MISMO modelo y la MISMA cuenta que la página (pulso_historial).
  2. A los que tienen lo más probable en 75 %+ (con su tramo medido de 100+ casos) les manda UN aviso al canal
     VIP de Telegram, una sola vez por partido y mercado (telegram_enviados).
  3. Pide a Gemini la mejor jugada, PERO SÓLO ENTRE LOS MERCADOS DEL PULSO, con su probabilidad: así lo que se
     apunta es medible. Se guarda en pulso_ia (una por partido y marcador: tras un gol se vuelve a preguntar) y
     la página la destaca como «en prueba».
  4. Al terminar cada partido liquida lo recomendado (marcador y córners finales) para medirlo.

Nunca lanza: lo que falla se salta y se reintenta a los 2 minutos."""
import datetime as dt
import html
import json
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

import pulso_historial as ph

logger = logging.getLogger('pulso_vivo')
SITIO = 'https://sharpicksapp.com/datos/'
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/%s/summary'
AVISO_MIN = 0.75                         # lo que merece aviso
CANDIDATO_MIN = 0.70                     # lo que se le pasa a la IA (lo mismo que «Candidatos Pulso»)
JUSTA_MIN = 1.15                         # lo que aún paga algo (como `mejor` de la página)
NOMBRE = {'gol': 'Cae otro gol', 'gol2': 'Caen 2 goles más', 'gol_l': 'Marca %L', 'gol_v': 'Marca %V',
          'cor1': '1 córner más', 'cor2': '2 córners más', 'cor3': '3 córners más'}
MERCADOS = ['gol', 'gol_l', 'gol_v', 'gol2', 'cor1', 'cor2', 'cor3']
CDMX = dt.timezone(dt.timedelta(hours=-6))


# ---------- la misma cuenta que la página ----------
def clave_modelo(M: Dict, k: str, f: Dict) -> str:
    """Qué tabla de «salió» toca: la del modelo sin fuerza previa si el partido no la tiene (web/pulso.js `clave`)."""
    return k + '_sf' if f.get('lh') is None and k in ph.TOPE_SF and (k + '_sf') in M['modelos'] else k


def tramo(M: Dict, k: str, p: float) -> Optional[Dict]:
    m = M['modelos'].get(k)
    if not m:
        return None
    t = next((x for x in m['tabla'] if x['desde'] <= p <= x['hasta']), None)
    return t if t and t['n'] >= 100 else None


def mercados(M: Dict, f: Dict) -> List[Dict]:
    out = []
    for k in MERCADOS:
        p = ph.prob(M, k, f)
        if p is None or (k == 'gol2' and p < 0.15):
            continue
        out.append({'k': k, 'p': p, 'tramo': tramo(M, clave_modelo(M, k, f), p)})
    return out


def mejor(ms: List[Dict]) -> Optional[Dict]:
    c = [m for m in ms if m['tramo'] and 1 / m['p'] >= JUSTA_MIN and m['p'] >= 0.6]
    return max(c, key=lambda m: m['p']) if c else None


def clave_partido(p: Dict) -> str:
    """La misma de la página (`clavePartido`) y de pulso_desbloqueos: deporte|a / b|día en CDMX."""
    L, _, V = str(p.get('partido') or '').partition(' vs ')
    return '|'.join([p.get('deporte') or '', ' / '.join(sorted([L.lower().strip(), V.lower().strip()])), dia(p)])


def dia(p: Dict) -> str:
    try:
        d = dt.datetime.strptime(str(p['inicio'])[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone.utc)
        return d.astimezone(CDMX).strftime('%Y-%m-%d')
    except Exception:
        return str(p.get('fecha') or '')


def nombre(k: str, p: Dict) -> str:
    L, _, V = str(p.get('partido') or '').partition(' vs ')
    return NOMBRE[k].replace('%L', L).replace('%V', V)


# ---------- ESPN en vivo ----------
def estado_vivo(d: Dict, girado: bool) -> Optional[Dict]:
    """Minuto, marcador, córners y lo principal, en el orden de NUESTRO «A vs B». None fuera del 2.º tiempo."""
    comp = ((d.get('header') or {}).get('competitions') or [{}])[0]
    st = comp.get('status') or {}
    tp = st.get('type') or {}
    cs = comp.get('competitors') or []
    h = next((c for c in cs if c.get('homeAway') == 'home'), {})
    a = next((c for c in cs if c.get('homeAway') == 'away'), {})
    ids = [str((h.get('team') or {}).get('id')), str((a.get('team') or {}).get('id'))]
    stats = {}
    for t in ((d.get('boxscore') or {}).get('teams') or []):
        lado = 0 if str((t.get('team') or {}).get('id')) == ids[0] else 1
        for s in t.get('statistics') or []:
            stats.setdefault(s.get('name'), [None, None])[lado] = s.get('displayValue')
    g = [int(h.get('score') or 0), int(a.get('score') or 0)]
    if girado:
        g = g[::-1]
        stats = {k: v[::-1] for k, v in stats.items()}
    fin = bool(tp.get('completed'))
    m = re.match(r"(\d+)", str(st.get('displayClock') or ''))
    t = float(m.group(1)) if m else None
    num = lambda x: float(str(x).replace('%', '')) if x not in (None, '') and re.match(r'^[\d.]+%?$', str(x)) else None
    cor = [num(x) for x in stats.get('wonCorners', [None, None])]
    return {'fase': tp.get('state'), 'periodo': int(st.get('period') or 0), 't': t, 'g': g, 'fin': fin,
            'c': int(cor[0] + cor[1]) if None not in cor else None, 'stats': stats}


# ---------- Supabase ----------
def _sb() -> Optional[Tuple[str, Dict]]:
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    return url.rstrip('/') + '/rest/v1/', {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}


def ya_avisados(s, sb) -> Optional[set]:
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat()
    r = s.get(sb[0] + 'telegram_enviados', headers=sb[1], timeout=30,
              params={'select': 'pick', 'tipo': 'eq.pulso', 'enviado': 'gte.' + desde, 'limit': 5000})
    return {x['pick'] for x in r.json()} if r.ok else None


def recomendaciones(s, sb, desde: str) -> Dict[Tuple[str, str], Dict]:
    r = s.get(sb[0] + 'pulso_ia', headers=sb[1], timeout=30, params={'select': '*', 'fecha': 'gte.' + desde, 'limit': 2000})
    return {(x['clave'], x['marcador']): x for x in r.json()} if r.ok else {}


# ---------- IA ----------
INSTRUCCION = (
    'Eres el analista en vivo de SharPicks. Te doy un partido de fútbol en el 2.º tiempo: minuto, marcador, '
    'estadísticas del momento y los mercados del Pulso con la probabilidad que da nuestro modelo (medido con '
    'miles de partidos) y lo que salió en el historial en ese tramo. Elige UNO de esos mercados: el que mejor '
    'combine probabilidad alta y lo que dicen las estadísticas del partido (quién ataca, tiros a puerta, '
    'córners, expulsados). No inventes mercados ni probabilidades. Escribe el motivo en español sencillo, en una '
    'sola frase de 160 caracteres como máximo, sin emojis.')


def preguntar_ia(p: Dict, e: Dict, ms: List[Dict]) -> Optional[Dict]:
    k = os.environ.get('GEMINI_API_KEY')
    if not k or not ms:
        return None
    import requests
    import ia_gemini
    claves = [m['k'] for m in ms]
    datos = {'partido': p['partido'], 'liga': p.get('liga'), 'minuto': e['t'], 'marcador': '%d-%d' % tuple(e['g']),
             'estadisticas': {n: v for n, v in e['stats'].items() if n in (
                 'totalShots', 'shotsOnTarget', 'wonCorners', 'possessionPct', 'redCards', 'saves', 'foulsCommitted')},
             'mercados': [{'mercado': m['k'], 'nombre': nombre(m['k'], p), 'prob_modelo': round(m['p'], 3),
                           'salio_historial': m['tramo']['fue'] if m['tramo'] else None} for m in ms]}
    esquema = {'type': 'OBJECT', 'properties': {'mercado': {'type': 'STRING', 'enum': claves}, 'motivo': {'type': 'STRING'}},
               'required': ['mercado', 'motivo']}
    cuerpo = {'systemInstruction': {'parts': [{'text': INSTRUCCION}]},
              'contents': [{'role': 'user', 'parts': [{'text': json.dumps(datos, ensure_ascii=False)}]}],
              'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json', 'responseSchema': esquema}}
    for modelo in ia_gemini.MODELOS:
        try:
            r = requests.post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % modelo,
                              params={'key': k}, json=cuerpo, timeout=45)
            if not r.ok:
                logger.warning('[pulso-ia] %s respondió %s', modelo, r.status_code)
                continue
            d = json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
            if d.get('mercado') in claves:
                return {'mercado': d['mercado'], 'motivo': str(d.get('motivo') or '')[:200], 'modelo_ia': modelo}
        except Exception as ex:
            logger.warning('[pulso-ia] %s: %s', modelo, type(ex).__name__)
    return None


def liquidar(rec: Dict, g_fin: List[int], c_fin: Optional[int]) -> Optional[bool]:
    gh, ga = (int(x) for x in rec['marcador'].split('-'))
    k = rec['mercado']
    if k.startswith('cor'):
        if c_fin is None or rec.get('corners') is None:
            return None
        return c_fin - rec['corners'] >= int(k[3])
    return {'gol': sum(g_fin) > gh + ga, 'gol2': sum(g_fin) - gh - ga >= 2,
            'gol_l': g_fin[0] > gh, 'gol_v': g_fin[1] > ga}.get(k)


# ---------- Telegram ----------
def texto_aviso(p: Dict, e: Dict, m: Dict, rec: Optional[Dict]) -> str:
    t = m['tramo']
    L, _, V = p['partido'].partition(' vs ')
    h = ['<b>Pulso SharPicks · en vivo</b>',
         '%s %d-%d %s · %d\'' % (html.escape(L), e['g'][0], e['g'][1], html.escape(V), e['t']),
         '<b>%s</b> · %d %% <i>(en el historial salió %d %%)</i>' % (html.escape(nombre(m['k'], p)), round(100 * m['p']), round(100 * t['fue']))]
    if rec and rec.get('mercado'):
        h.append('IA + modelo (en prueba): <b>%s</b>. %s' % (html.escape(nombre(rec['mercado'], p)), html.escape(rec.get('motivo') or '')))
    h.append('Lo más probable ahora según lo medido; la casa puede pagar poco. Ábrelo en sharpicksapp.com')
    return '\n'.join(h)


def enviar(texto: str) -> bool:
    chat = os.environ.get('TELEGRAM_CHAT_VIP')
    if not chat or not os.environ.get('TELEGRAM_BOT_TOKEN'):
        return False
    import bot_telegram as bt
    r, motivo = bt._post('sendMessage', timeout=30, json={'chat_id': chat, 'text': texto, 'parse_mode': 'HTML',
                                                          'disable_web_page_preview': True})
    if r is None or not r.ok:
        logger.warning('[pulso] telegram: %s', motivo)
        return False
    return True


# ---------- una vuelta ----------
def partidos(s) -> List[Dict]:
    out, vistos = [], set()
    for f, k in (('hoy.json', 'picks'), ('analisis.json', 'analisis')):
        try:
            for p in s.get(SITIO + f, params={'t': int(time.time())}, timeout=30).json().get(k) or []:
                if p.get('deporte') != 'Fútbol' or ':' not in str(p.get('espn') or ''):
                    continue
                c = clave_partido(p)
                if c in vistos:
                    continue
                vistos.add(c)
                out.append(p)
        except Exception as ex:
            logger.warning('[pulso] sin %s: %s', f, ex)
    return out


def en_juego(p: Dict, ahora: dt.datetime) -> bool:
    try:
        ini = dt.datetime.strptime(str(p['inicio'])[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone.utc)
    except Exception:
        return False
    return ini - dt.timedelta(minutes=5) <= ahora <= ini + dt.timedelta(hours=2, minutes=45)


def vuelta(s, M: Dict, sb, seco: bool = False) -> Dict:
    ahora = dt.datetime.now(dt.timezone.utc)
    hoy = (ahora.astimezone(CDMX) - dt.timedelta(days=1)).strftime('%Y-%m-%d')
    lista = [p for p in partidos(s) if en_juego(p, ahora)]
    avisados = set() if seco else (ya_avisados(s, sb) if sb else None)
    recs = recomendaciones(s, sb, hoy) if sb else {}
    res = {'en_juego': len(lista), 'segundo_tiempo': 0, 'avisos': 0, 'ia': 0, 'liquidadas': 0}
    for p in lista:
        ruta, ev = str(p['espn']).split(':', 1)
        try:
            e = estado_vivo(s.get(ESPN % ruta, params={'event': ev}, timeout=20).json(), bool(p.get('girado')))
        except Exception:
            continue
        if not e:
            continue
        clave = clave_partido(p)
        if e['fin'] and sb:                                   # 4. liquidar lo recomendado de este partido
            for (c, _), rec in recs.items():
                if c == clave and rec.get('acierto') is None:
                    ok = liquidar(rec, e['g'], e['c'])
                    if ok is not None and not seco:
                        s.patch(sb[0] + 'pulso_ia', headers=dict(sb[1], Prefer='return=minimal'), timeout=30,
                                params={'clave': 'eq.' + c, 'marcador': 'eq.' + rec['marcador']}, json={'acierto': ok})
                        res['liquidadas'] += 1
            continue
        if e['fase'] != 'in' or e['periodo'] != 2 or e['t'] is None:
            continue
        res['segundo_tiempo'] += 1
        f = ph.rasgos(M, p.get('ctx') or {}, e['t'], e['g'][0], e['g'][1], e['c'])
        ms = mercados(M, f)
        m = mejor(ms)
        if not m or m['p'] < CANDIDATO_MIN:
            continue
        marc = '%d-%d' % tuple(e['g'])
        rec = recs.get((clave, marc))
        if rec is None and sb is not None:                    # 3. la IA, una vez por partido y marcador
            opciones = [x for x in ms if x['tramo'] and x['p'] >= 0.6]
            r = preguntar_ia(p, e, opciones)
            if r:
                elegido = next(x for x in opciones if x['k'] == r['mercado'])
                rec = dict(r, clave=clave, partido=p['partido'], fecha=dia(p), marcador=marc, minuto=int(e['t']),
                           prob=round(elegido['p'], 3), corners=e['c'])
                if not seco:
                    s.post(sb[0] + 'pulso_ia', headers=dict(sb[1], Prefer='resolution=ignore-duplicates,return=minimal'),
                           timeout=30, json=rec)
                recs[(clave, marc)] = rec
                res['ia'] += 1
        if m['p'] >= AVISO_MIN and avisados is not None:      # 2. el aviso, una vez por partido y mercado
            pick = 'pulso|%s|%s' % (clave, m['k'])
            if pick in avisados:
                continue
            txt = texto_aviso(p, e, m, rec)
            if seco:
                print(txt + '\n')
                continue
            if enviar(txt):
                s.post(sb[0] + 'telegram_enviados', headers=dict(sb[1], Prefer='resolution=ignore-duplicates,return=minimal'),
                       timeout=30, json=[{'pick': pick, 'canal': 'vip', 'tipo': 'pulso', 'texto': nombre(m['k'], p),
                                          'partido': p['partido'], 'inicio': str(p['inicio'])}])
                avisados.add(pick)
                res['avisos'] += 1
    return res


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    seco = '--seco' in sys.argv
    minutos = 0
    if '--minutos' in sys.argv:
        minutos = int(sys.argv[sys.argv.index('--minutos') + 1])
    import requests
    s = requests.Session()
    with open(ph.MODELO, encoding='utf-8') as fh:
        M = json.load(fh)
    sb = _sb()
    if sb is None and not seco:
        print('pulso: sin Supabase no se sabe qué ya se avisó: no se manda nada')
        return 0
    hasta = time.time() + minutos * 60
    while True:
        try:
            r = vuelta(s, M, sb, seco)
            print('pulso %s: %s' % (dt.datetime.now(dt.timezone.utc).strftime('%H:%M'), r), flush=True)
        except Exception as ex:
            logger.warning('[pulso] vuelta: %s', ex)
            r = {'en_juego': 1}
        # sin nada en juego, no se tiene ocupado el runner (el despertador lo vuelve a lanzar a la hora)
        if time.time() + 120 > hasta or not r.get('en_juego'):
            return 0
        time.sleep(120)


if __name__ == '__main__':
    raise SystemExit(main())
