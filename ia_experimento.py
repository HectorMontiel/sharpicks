#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v588 — ¿LA IA SABE ALGO QUE LA CUOTA NO? EL EXPERIMENTO A CIEGAS.

Medido el 6-nov-2026: la IA recibía la cuota y nuestra probabilidad, y se les pegaba (daba 3+ puntos más que la cuota en menos
de 1 % de los picks). Una IA que copia al precio no puede subir el acierto.

Aquí lee sólo las noticias guardadas ANTES del partido y cada pick como texto. No recibe cuota, probabilidad, nivel, resultado
ni datos del partido. Contesta qué tanto ayudan o estorban esas noticias a cada pick (−2 a +2) y qué factor lo explica. Eso se
guarda aparte, en `ia_experimento`; nadie lo ve. `mediciones/medir_ia_experimento.py` decide si suma a igual cuota.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Dict, List

import requests

VERSION = 'noticias-v1'
MODELO = 'gemini-flash-lite-latest'
LOTE = 8
PAUSA_S = 4.5
TOPE_S = int(os.environ.get('EXP_TOPE_S', '3000'))
MAX_CONSULTAS = int(os.environ.get('EXP_MAX', '150'))
FACTORES = ['baja_clave_favorecido', 'baja_clave_rival', 'rotacion_o_descanso', 'calendario_o_viaje', 'motivacion', 'cambio_de_tecnico', 'clima_o_cancha', 'otro', 'ninguno']
logger = logging.getLogger(__name__)

INSTRUCCION = (
    'Eres un analista que SOLO lee noticias deportivas previas a un partido. Recibes partidos con sus titulares y las apuestas a evaluar. '
    'No conoces cuotas, probabilidades ni el resultado, y no debes adivinarlos ni usar lo que recuerdes de esos equipos. '
    'Para cada apuesta, di si los titulares la favorecen o la perjudican: "impacto" entero de -2 a 2. '
    '0: los titulares no dicen nada útil para esa apuesta (es lo normal; úsalo siempre que dudes). '
    '-1 o +1: hecho concreto de efecto moderado. -2 o +2: hecho concreto y fuerte, como la baja confirmada de un jugador clave. '
    'Piensa en la apuesta exacta: una baja del goleador perjudica «Goles X: Más de 0.5» y favorece «Goles: Menos de 2.5». '
    'Ignora titulares de otro equipo con nombre parecido, de la rama femenil o varonil contraria, de otra competición o de opinión sin hechos. '
    '"factores": los que apliquen de la lista. "nota": el hecho en una frase breve, o vacío si el impacto es 0. No inventes nada que no esté en los titulares. '
    'Responde un elemento por cada apuesta, copiando "i" y "j".'
)
ESQUEMA = {'type': 'OBJECT', 'properties': {'r': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
    'i': {'type': 'INTEGER'}, 'j': {'type': 'INTEGER'}, 'impacto': {'type': 'INTEGER'},
    'factores': {'type': 'ARRAY', 'items': {'type': 'STRING', 'enum': FACTORES}}, 'nota': {'type': 'STRING'}},
    'required': ['i', 'j', 'impacto', 'factores', 'nota']}}}, 'required': ['r']}


def _base():
    u, k = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not u or not k:
        raise SystemExit('faltan los secretos de Supabase')
    return u.rstrip('/') + '/rest/v1/', {'apikey': k, 'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'}


def _todas(base, h, tabla, params) -> List[Dict]:
    filas = []
    for i in range(100):
        r = requests.get(base + tabla, headers=h, timeout=60, params=dict(params, limit=1000, offset=i * 1000))
        r.raise_for_status()
        lote = r.json()
        filas += lote
        if len(lote) < 1000:
            return filas
    return filas


def partidos_a_preguntar(analisis: List[Dict], picks: List[Dict], reales: Dict, hechos: set) -> List[Dict]:
    """Sólo partidos ya resueltos, analizados antes de empezar y con noticias. La entrada lleva el texto del pick y nada de cuota, prob ni resultado."""
    por = {}
    for p in picks:
        if p.get('estado') in ('verde', 'roja') and p.get('tipo') not in ('combinada', 'error'):
            por.setdefault((p['fecha'], p['partido']), []).append(reales.get(p['id'], p['apuesta']))
    salida = []
    for a in analisis:
        if not a.get('noticias') or not a.get('creado') or not a.get('inicio') or str(a['creado'])[:16].replace('T', ' ') >= str(a['inicio'])[:16].replace('T', ' '):
            continue
        ap = sorted({x for x in por.get((a['fecha'], a['partido']), []) if x and '🔒' not in x and (a['fecha'], a['partido'], x) not in hechos})
        if ap:
            salida.append({'fecha': a['fecha'], 'partido': a['partido'], 'liga': a.get('liga'), 'deporte': a.get('deporte'),
                           'titulares': [n for n in str(a['noticias']).split(' | ') if n], 'apuestas': ap})
    return sorted(salida, key=lambda m: (m['fecha'], m['partido']))


def entrada(lote: List[Dict]) -> List[Dict]:
    return [{'i': i, 'partido': m['partido'], 'liga': m['liga'], 'deporte': m['deporte'], 'fecha': m['fecha'], 'titulares': m['titulares'],
             'apuestas': [{'j': j, 'texto': a} for j, a in enumerate(m['apuestas'])]} for i, m in enumerate(lote)]


def filas_de_respuesta(lote: List[Dict], respuesta: List[Dict]) -> List[Dict]:
    filas = {}
    for x in respuesta:
        i, j = x.get('i'), x.get('j')
        if not isinstance(i, int) or not isinstance(j, int) or not 0 <= i < len(lote) or not 0 <= j < len(lote[i]['apuestas']):
            continue
        imp = x.get('impacto')
        if not isinstance(imp, int) or not -2 <= imp <= 2:
            continue
        m = lote[i]
        filas[(i, j)] = {'version': VERSION, 'fecha': m['fecha'], 'partido': m['partido'], 'apuesta': m['apuestas'][j], 'impacto': imp,
                         'factores': [f for f in (x.get('factores') or []) if f in FACTORES], 'nota': str(x.get('nota') or '')[:240], 'modelo': MODELO}
    return list(filas.values())


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise SystemExit('falta GEMINI_API_KEY')
    base, h = _base()
    analisis = _todas(base, h, 'ia_analisis', {'select': 'fecha,partido,liga,deporte,noticias,creado,inicio', 'noticias': 'not.is.null', 'order': 'id'})
    picks = _todas(base, h, 'picks', {'select': 'id,fecha,partido,apuesta,estado,tipo', 'estado': 'in.(verde,roja)', 'order': 'id'})
    reales = {x['id']: x['apuesta'] for x in _todas(base, h, 'picks_premium', {'select': 'id,apuesta', 'order': 'id'})}
    hechos = {(x['fecha'], x['partido'], x['apuesta']) for x in _todas(base, h, 'ia_experimento', {'select': 'fecha,partido,apuesta', 'version': 'eq.' + VERSION, 'order': 'fecha,partido,apuesta'})}
    lista = partidos_a_preguntar(analisis, picks, reales, hechos)
    print('experimento: %d partidos por leer, %d apuestas ya leídas' % (len(lista), len(hechos)))
    ini, consultas, guardadas, fallos = time.monotonic(), 0, 0, 0
    for a in range(0, len(lista), LOTE):
        if consultas >= MAX_CONSULTAS or time.monotonic() - ini > TOPE_S or fallos >= 5:
            break
        lote = lista[a:a + LOTE]
        cuerpo = {'systemInstruction': {'parts': [{'text': INSTRUCCION}]}, 'contents': [{'role': 'user', 'parts': [{'text': json.dumps(entrada(lote), ensure_ascii=False)}]}],
                  'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json', 'responseSchema': ESQUEMA}}
        consultas += 1
        try:
            r = requests.post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % MODELO, params={'key': key}, json=cuerpo, timeout=90)
            if r.status_code == 429:
                print('experimento: sin cupo; sigue en otra corrida')
                break
            r.raise_for_status()
            filas = filas_de_respuesta(lote, json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']).get('r') or [])
            if filas:
                u = requests.post(base + 'ia_experimento', headers=dict(h, Prefer='resolution=merge-duplicates,return=minimal'), json=filas, timeout=60)
                u.raise_for_status()
                guardadas += len(filas)
            fallos = 0
        except Exception as e:      # el texto de la excepción podría llevar la URL con la clave: sólo el tipo
            fallos += 1
            logger.warning('experimento: %s', type(e).__name__)
            time.sleep(10)
        time.sleep(PAUSA_S)
    print('experimento: %d consultas, %d apuestas guardadas, %.0f s' % (consultas, guardadas, time.monotonic() - ini))
    return 0


# v589 — EN VIVO, Y CON MEJORES FUENTES. En el pasado sólo había titulares del partido y en 850 de 910 picks no decían nada (impacto 0). Antes de
# cada partido se le da a la misma IA a ciegas lo que sí mueve un resultado: las bajas por equipo (FotMob en fútbol, reporte de ESPN en NBA/NHL/NFL)
# y noticias buscadas por equipo. Se guarda aparte; nadie lo ve. No se enseña hasta que pase `mediciones/medir_ia_experimento.py`.
VERSION_VIVO = 'vivo-v1'
LOTE_VIVO = 6
MAX_VIVO = int(os.environ.get('EXP_MAX_VIVO', '25'))
HORAS_VIVO = 14
CUPO_VIVO = 300            # no le quita cupo a los análisis ni al Pulso
TOPE_VIVO_S = 300
RUTAS_ESPN = {'NBA': 'basketball/nba', 'NHL': 'hockey/nhl', 'NFL': 'football/nfl'}
BUSQUEDA_BAJAS = '"%s" (lesión OR baja OR bajas OR lesionado OR suspendido OR duda OR rotación OR injury OR injured OR out) when:3d%s'


def lesiones_espn(deporte: str, cache: Dict) -> Dict:
    """{equipo: ['Jugador (Out): comentario']} del reporte de lesiones de ESPN; {} si no hay."""
    ruta = RUTAS_ESPN.get(deporte)
    if not ruta:
        return {}
    if deporte not in cache:
        cache[deporte] = {}
        try:
            d = requests.get('https://site.api.espn.com/apis/site/v2/sports/%s/injuries' % ruta, timeout=20).json()
            for eq in d.get('injuries') or []:
                cache[deporte][eq.get('displayName')] = ['%s (%s): %s' % ((x.get('athlete') or {}).get('displayName', '?'), x.get('status', '?'), str(x.get('shortComment') or '')[:110])
                                                         for x in (eq.get('injuries') or [])[:8]]
        except Exception as e:
            logger.warning('experimento: lesiones %s: %s', deporte, type(e).__name__)
    return cache[deporte]


def bajas_fotmob(partido: str, tabla: Dict) -> Dict:
    h, _, a = partido.partition(' vs ')
    for k, v in tabla.items():
        if k.split('|')[1:] == [h.strip(), a.strip()]:
            return {lado: ['%s (%s)' % (b.get('jugador'), b.get('tipo')) for b in ((v.get(lado) or {}).get('bajas') or [])[:10]] for lado in ('home', 'away')}
    return {}


def titulares_de_bajas(equipo: str, liga, inicio, fem_extra: str = '') -> List[str]:
    """Búsqueda por equipo y por bajas; sólo lo publicado antes de empezar."""
    import email.utils
    import xml.etree.ElementTree as ET
    import datetime as dt
    import ia_gemini as g
    try:
        r = requests.get(g.RSS_URL, params={'q': BUSQUEDA_BAJAS % (g._nombre_busqueda(equipo), fem_extra), 'hl': 'es-419', 'gl': 'MX', 'ceid': 'MX:es-419'},
                         timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        items = ET.fromstring(r.text).findall('.//item') if r.ok else []
    except Exception:
        return []
    fuera = []
    for it in items:
        try:
            pub = email.utils.parsedate_to_datetime(it.findtext('pubDate') or '')
        except Exception:
            pub = None
        if inicio and pub and pub >= inicio:
            continue
        t = (it.findtext('title') or '').rpartition(' - ')[0].strip() or (it.findtext('title') or '').strip()
        if t and not g._SIN_INFO.search(t) and bool(g._TITULAR_FEM.search(t)) == bool(fem_extra) and t not in fuera:
            fuera.append(t[:160])
        if len(fuera) >= 4:
            break
    return fuera


def entrada_vivo(m: Dict) -> Dict:
    """Lo único que ve: equipos, liga, bajas, titulares y el texto de cada apuesta. Sin cuota, probabilidad, nivel ni nada nuestro."""
    return {'partido': m['partido'], 'liga': m.get('liga'), 'deporte': m.get('deporte'), 'fecha': m['fecha'], 'bajas': m.get('bajas') or {}, 'titulares': m.get('titulares') or [], 'apuestas': m['apuestas']}


def vivo() -> int:
    import datetime as dt
    import escudos
    import ia_gemini as g
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        return 0
    base, h = _base()
    sb = (base + 'ia_analisis', h)
    ahora = dt.datetime.now(dt.timezone.utc)
    g.leer_uso_de_hoy(sb, ahora)
    picks = json.load(open(g.DATOS, encoding='utf-8')).get('picks') or []
    try:
        reales = json.load(open(g.PRIVADO, encoding='utf-8'))
    except Exception:
        reales = {}
    try:
        tabla = json.load(open('bajas_dia.json', encoding='utf-8')).get('partidos') or {}
    except Exception:
        tabla = {}
    hechos = {(x['fecha'], x['partido'], x['apuesta']) for x in _todas(base, h, 'ia_experimento', {'select': 'fecha,partido,apuesta', 'version': 'eq.' + VERSION_VIVO,
                                                                                                  'fecha': 'gte.' + (ahora - dt.timedelta(days=2)).strftime('%Y-%m-%d'), 'order': 'fecha,partido,apuesta'})}
    por = {}
    for p in picks:
        ini = g._utc(p.get('inicio'))
        ap = reales.get(p.get('id'), p.get('apuesta'))
        if (p.get('estado') != 'pendiente' or p.get('solo_analisis') or p.get('tipo') in ('combinada', 'error') or ini is None or not ap or '🔒' in ap
                or not ahora < ini <= ahora + dt.timedelta(hours=HORAS_VIVO) or (p.get('fecha'), p.get('partido'), ap) in hechos):
            continue
        m = por.setdefault((p['fecha'], p['partido']), {'fecha': p['fecha'], 'partido': p['partido'], 'liga': p.get('liga'), 'deporte': str(p.get('deporte') or 'Fútbol'), 'ini': ini, 'apuestas': []})
        if ap not in m['apuestas']:
            m['apuestas'].append(ap)
    lista = sorted(por.values(), key=lambda m: m['ini'])
    ini_paso, consultas, guardadas, cache = time.monotonic(), 0, 0, {}
    for a in range(0, len(lista), LOTE_VIVO):
        gastado = g.USADAS_HOY['lite'] + sum(u['llamadas'] for (mo, _), u in g.USO.items() if mo == g.MODELO_CUPO)
        if consultas >= MAX_VIVO or gastado >= CUPO_VIVO or time.monotonic() - ini_paso > TOPE_VIVO_S:
            break
        lote = lista[a:a + LOTE_VIVO]
        for m in lote:
            casa, _, visita = m['partido'].partition(' vs ')
            les = lesiones_espn(m['deporte'], cache)
            m['bajas'] = ({'home': les.get(casa.strip(), []), 'away': les.get(visita.strip(), [])} if les else bajas_fotmob(m['partido'], tabla)) if m['deporte'] != 'Tenis' else {}
            try:
                fem = ' femenil' if escudos._cat(m.get('liga'), casa, visita)[0] else ''
            except Exception:
                fem = ''
            m['titulares'] = [t for eq in (casa, visita) if eq.strip() for t in titulares_de_bajas(eq.strip(), m.get('liga'), m['ini'], fem)]
        paquete = [dict(entrada_vivo(m), i=i, apuestas=[{'j': j, 'texto': x} for j, x in enumerate(m['apuestas'])]) for i, m in enumerate(lote)]
        cuerpo = {'systemInstruction': {'parts': [{'text': INSTRUCCION + ' "bajas" trae a los ausentes de cada lado ("home" es el local); pesa sólo los que sepas por el dato que sean importantes, sin inventar.'}]},
                  'contents': [{'role': 'user', 'parts': [{'text': json.dumps(paquete, ensure_ascii=False)}]}],
                  'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json', 'responseSchema': ESQUEMA}}
        consultas += 1
        try:
            r = requests.post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % MODELO, params={'key': key}, json=cuerpo, timeout=90)
            g._contar(MODELO, 'ciega', r.ok, r.status_code == 429)
            if r.status_code == 429:
                break
            r.raise_for_status()
            filas = filas_de_respuesta(lote, json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']).get('r') or [])
            for f in filas:
                m = next(x for x in lote if x['partido'] == f['partido'] and x['fecha'] == f['fecha'])
                f.update(version=VERSION_VIVO, datos=json.dumps({'bajas': m['bajas'], 'titulares': m['titulares']}, ensure_ascii=False)[:3000])
            if filas:
                requests.post(base + 'ia_experimento', headers=dict(h, Prefer='resolution=merge-duplicates,return=minimal'), json=filas, timeout=60).raise_for_status()
                guardadas += len(filas)
        except Exception as e:      # sólo el tipo: el texto podría llevar la clave en la URL
            logger.warning('experimento: %s', type(e).__name__)
        time.sleep(PAUSA_S)
    g.guardar_uso(sb, ahora)
    print('experimento en vivo: %d partidos, %d consultas, %d apuestas guardadas' % (len(lista), consultas, guardadas))
    return 0


if __name__ == '__main__':
    raise SystemExit(vivo() if '--vivo' in sys.argv else main())
