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


if __name__ == '__main__':
    raise SystemExit(main())
