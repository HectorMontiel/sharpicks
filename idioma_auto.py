#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v590 — EL INGLÉS SE ESCRIBE SOLO. La app se escribe en español; al subir un texto nuevo, esto lo traduce y lo agrega a `web/idioma_en.js`.

El usuario: «todo lo que sea texto se tiene que modificar en español y en inglés; si hay forma de hacerlo automático, que así sea». Encuentra lo que falta con
el mismo extractor de `test_v582.py`. Una respuesta mala no entra: los `#` deben cuadrar y no puede venir vacía. Si una traducción ya existe, nunca se pisa,
así que corregir una a mano en el diccionario es definitivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, List

import requests

import test_v582 as t

MODELO = 'gemini-flash-lite-latest'
LOTE = 40
RUTA = os.path.join(t.W, 'idioma_en.js')
GLOSARIO = {'Combinada': 'Parlay', 'Cuota': 'Odds', 'Verde': 'Win', 'Roja': 'Loss', 'Fútbol': 'Soccer', 'Más de': 'Over', 'Menos de': 'Under', 'Monedas': 'Coins', 'Pick': 'Pick',
            'Mi cuenta': 'My account', 'Planes': 'Plans', 'Historial': 'History', 'Ambos anotan': 'Both teams to score', 'Córners': 'Corners', 'Hándicap': 'Handicap', 'Plata': 'Silver',
            'Oro': 'Gold', 'Platino': 'Platinum', 'Diamante': 'Diamond', 'Cuota alta': 'High odds', 'IA': 'AI'}
INSTRUCCION = ('Translate these interface texts of a sports forecasting app from Mexican Spanish into natural, short American English. Keep the same meaning, tone and punctuation. '
               'The symbol # is a number: keep exactly the same number of # in the same logical place. Keep emojis and proper names. Never promise winnings. '
               'Use this glossary: %s. Return one item per text with its index "i".' % json.dumps(GLOSARIO, ensure_ascii=False))
ESQUEMA = {'type': 'OBJECT', 'properties': {'r': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'i': {'type': 'INTEGER'}, 'en': {'type': 'STRING'}}, 'required': ['i', 'en']}}}, 'required': ['r']}


def llave(texto: str) -> str:
    return re.sub(r'\d+(?:[.,]\d+)?', '#', t.nucleo(texto))


def faltantes() -> List[str]:
    """Las llaves nuevas, ya sin puntuación en la orilla y con # en vez de números."""
    d = t.diccionario()
    salida = set()
    for x in t.textos():
        c = t.nucleo(x)
        if t.NO_SE_VE.search(x) or not c or c in d or llave(x) in d or c[:1].upper() + c[1:] in d:
            continue
        salida.add(llave(x))
    return sorted(salida)


def valida(clave: str, en) -> bool:
    if not isinstance(en, str):
        return False
    en = t.nucleo(en.strip())
    return bool(en) and clave.count('#') == en.count('#')


def agrega(texto_js: str, nuevas: Dict[str, str]) -> str:
    """Agrega al final sin tocar lo que ya hay: lo existente nunca se pisa."""
    i = texto_js.rindex('}')
    cuerpo = texto_js[:i].rstrip()
    actuales = json.loads(texto_js[texto_js.index('{'):i + 1])
    lineas = ['%s: %s' % (json.dumps(k, ensure_ascii=False), json.dumps(t.nucleo(v.strip()), ensure_ascii=False)) for k, v in sorted(nuevas.items()) if k not in actuales]
    if not lineas:
        return texto_js
    fin = '\r\n' if '\r\n' in texto_js else '\n'
    return cuerpo + ',' + fin + (',' + fin).join(lineas) + fin + texto_js[i:]


def traduce(textos: List[str], key: str) -> Dict[str, str]:
    salida = {}
    for a in range(0, len(textos), LOTE):
        lote = textos[a:a + LOTE]
        cuerpo = {'systemInstruction': {'parts': [{'text': INSTRUCCION}]}, 'contents': [{'role': 'user', 'parts': [{'text': json.dumps([{'i': i, 'es': x} for i, x in enumerate(lote)], ensure_ascii=False)}]}],
                  'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json', 'responseSchema': ESQUEMA}}
        r = requests.post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % MODELO, params={'key': key}, json=cuerpo, timeout=90)
        if not r.ok:
            print('idioma: Gemini respondió %s' % r.status_code)
            continue
        for x in json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']).get('r') or []:
            i = x.get('i')
            if isinstance(i, int) and 0 <= i < len(lote) and valida(lote[i], x.get('en')):
                salida[lote[i]] = x['en']
    return salida


def main() -> int:
    falta = faltantes()
    print('idioma: %d textos sin inglés' % len(falta))
    if not falta:
        return 0
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        print('idioma: sin GEMINI_API_KEY; se queda pendiente')
        return 0
    nuevas = traduce(falta, key)
    with open(RUTA, encoding='utf-8', newline='') as h:
        js = h.read()
    with open(RUTA, 'w', encoding='utf-8', newline='') as h:
        h.write(agrega(js, nuevas))
    print('idioma: %d traducidos; quedan %d' % (len(nuevas), len(falta) - len(nuevas)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
