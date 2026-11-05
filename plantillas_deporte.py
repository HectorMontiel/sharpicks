#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v568 — LA PLANTILLA DEL ANÁLISIS DE CADA DEPORTE, CON LOS MERCADOS QUE PLAYDOIT SÍ OFRECE.

El usuario: «en el análisis de IA usa prácticamente el mismo template que en fútbol y obviamente no debería: se apuesta distinto en
cada deporte. Checa los mercados y desarma las plantillas». Revisados en Playdoit el 5-nov-2026 (D:/Claude/mediciones/mercados_deportes.txt).
Cada mercado: (clave, cómo se llama, tipo).
  tipo: 'ou' más o menos con línea · 'lado' local o visita · 'lado3' local, empate o visita · 'hand' equipo con línea · 'sino' sí o no
En `etiqueta`, «%L» y «%V» son los equipos. La IA contesta en `mercados`: [{clave, seleccion, linea, prob}] y aquí se vuelve texto.
"""
from typing import Dict, List, Optional

PLANTILLAS: Dict[str, Dict] = {
    'NHL': {'mercados': [
        ('total', 'Total de goles', 'ou'), ('hand', 'Hándicap', 'hand'), ('r60', 'Resultado a 60 minutos', 'lado3'),
        ('gl', 'Goles de %L', 'ou'), ('gv', 'Goles de %V', 'ou'), ('primero', 'Primer gol', 'lado'),
        ('prorroga', '¿Habrá prórroga?', 'sino'), ('p1total', '1.er periodo: total de goles', 'ou'), ('p1', '1.er periodo: resultado', 'lado3')],
        'guia': 'En la NHL un partido empatado a 60 minutos va a prórroga y penales: «Resultado a 60 minutos» sí admite empate (suele rondar 20-25 %). '
                'El hándicap normal es ±1.5 y un equipo que gana por 1 no lo cubre. El total suele estar entre 5.5 y 6.5; en el 1.er periodo, entre 0.5 y 1.5. '
                'Fíjate en tiros, power play, goles por periodo y si anota primero.'},
    'NBA': {'mercados': [
        ('hand', 'Hándicap', 'hand'), ('total', 'Total de puntos', 'ou'), ('gl', 'Puntos de %L', 'ou'), ('gv', 'Puntos de %V', 'ou'),
        ('h1', '1.ª mitad: ganador', 'lado'), ('h1total', '1.ª mitad: total de puntos', 'ou'), ('q1total', '1.er cuarto: total de puntos', 'ou'),
        ('triples', 'Triples del partido', 'ou'), ('asist', 'Asistencias del partido', 'ou'), ('prorroga', '¿Habrá prórroga?', 'sino')],
        'guia': 'En la NBA no hay empate. Los totales rondan 210-240 puntos, la 1.ª mitad 105-120 y el 1.er cuarto 52-60; el hándicap va de 1.5 a 15. '
                'Fíjate en ritmo, puntos a favor y en contra, triples y descanso si viene en las noticias.'},
    'NFL': {'mercados': [
        ('hand', 'Hándicap', 'hand'), ('total', 'Total de puntos', 'ou'), ('gl', 'Puntos de %L', 'ou'), ('gv', 'Puntos de %V', 'ou'),
        ('h1', '1.ª mitad: ganador', 'lado'), ('h1total', '1.ª mitad: total de puntos', 'ou'), ('q1total', '1.er cuarto: total de puntos', 'ou'),
        ('td', 'Touchdowns del partido', 'ou'), ('fg', 'Goles de campo del partido', 'ou'), ('primero', 'Primer equipo en anotar', 'lado')],
        'guia': 'En la NFL el marcador avanza de 3 y de 7: las diferencias de 3 y de 7 son las más comunes. Los totales rondan 38-52 puntos, la 1.ª mitad 19-26, '
                'los touchdowns 3.5-5.5 y los goles de campo 2.5-3.5. Fíjate en yardas, pérdidas de balón y sacks.'},
    'MLB': {'mercados': [
        ('hand', 'Hándicap (run line)', 'hand'), ('total', 'Total de carreras', 'ou'), ('gl', 'Carreras de %L', 'ou'), ('gv', 'Carreras de %V', 'ou')],
        'guia': 'En el béisbol no hay empate y el hándicap normal es ±1.5 carreras. Los totales rondan 7.5-10.5. Fíjate en carreras a favor y en contra, hits y errores.'},
    'Tenis': {'mercados': [
        ('hand', 'Hándicap de sets', 'hand'), ('hjuegos', 'Hándicap de juegos', 'hand'), ('juegos', 'Total de juegos', 'ou'), ('jl', 'Juegos de %L', 'ou'), ('jv', 'Juegos de %V', 'ou'),
        ('s1', '1.er set: ganador', 'lado'), ('s1juegos', '1.er set: total de juegos', 'ou'), ('ambos', 'Ambos ganan un set', 'sino'),
        ('aces', 'Total de aces', 'ou'), ('breaks', 'Total de quiebres', 'ou'), ('df', 'Total de dobles faltas', 'ou')],
        'guia': 'En el tenis no hay empate. El hándicap de sets es ±1.5 y el total de juegos a 3 sets suele estar entre 20.5 y 23.5. En promedios_*: pg=partidos ganados, sf y sc=sets a favor y en contra, jt=juegos por partido, '
                'jf y jc=juegos a favor y en contra, s1=gana el 1.er set, s1j=juegos del 1.er set, s3=partidos a 3 sets, ace, df=dobles faltas, qb=quiebres, pts=puntos ganados.'},
}
PLANTILLAS['KBO'] = PLANTILLAS['MLB']
# v568 — el béisbol de invierno: Playdoit sólo da ganador, hándicap y total
PLANTILLAS['Béisbol'] = {'mercados': PLANTILLAS['MLB']['mercados'][:2], 'guia': PLANTILLAS['MLB']['guia'] + ' En promedios_*: gf y gc=carreras a favor y en contra, tot=carreras del partido, '
                           'pg=partidos ganados, h15=gana por 2 o más (cubre -1.5), o95=partidos con +9.5 carreras, f5=carreras en 5 entradas.'}


def texto_para_ia(deporte: str) -> str:
    """La parte de la instrucción con los mercados de ese deporte."""
    pl = PLANTILLAS.get(deporte)
    if not pl:
        return ''
    filas = []
    for clave, nombre, tipo in pl['mercados']:
        que = {'ou': 'seleccion "mas" o "menos" y linea (termina en .5)', 'lado': 'seleccion "local" o "visita"', 'lado3': 'seleccion "local", "empate" o "visita"',
               'hand': 'seleccion "local" o "visita" y linea del equipo elegido (por ejemplo -1.5 o +1.5)', 'sino': 'seleccion "si" o "no"'}[tipo]
        filas.append('"%s" (%s): %s' % (clave, nombre.replace('%L', 'local').replace('%V', 'visita'), que))
    return (' MERCADOS DE ESTE DEPORTE: en "mercados" da tu predicción de CADA UNO de estos, los que de verdad se apuestan aquí, con su probabilidad (prob, 0 a 1): ' +
            '; '.join(filas) + '. Usa las líneas de la casa si te las damos; si no, la línea .5 más cercana a tu estimación. Usa "promedios_local" y "promedios_visita" si vienen: son '
            'reales, de sus últimos partidos. ' + pl['guia'])


def _linea(x) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if abs(v) < 500 else None


def normaliza(deporte: str, crudo, L: str, V: str) -> Optional[List[Dict]]:
    """[{k, t, v, p}] en el orden de la plantilla: lo que se guarda y enseña. Lo que no tiene sentido se descarta, sin inventar."""
    pl = PLANTILLAS.get(deporte)
    if not pl or not isinstance(crudo, list):
        return None
    por = {str(x.get('clave')): x for x in crudo if isinstance(x, dict)}
    out = []
    for clave, nombre, tipo in pl['mercados']:
        x = por.get(clave)
        if not x:
            continue
        sel, lin = str(x.get('seleccion') or '').strip().lower(), _linea(x.get('linea'))
        if tipo == 'ou':
            if sel not in ('mas', 'menos') or lin is None or lin <= 0:
                continue
            txt = ('Más de ' if sel == 'mas' else 'Menos de ') + ('%g' % lin)
        elif tipo == 'hand':
            if sel not in ('local', 'visita') or lin is None:
                continue
            txt = '%s %s%g' % (L if sel == 'local' else V, '+' if lin > 0 else '', lin)
        elif tipo == 'sino':
            if sel not in ('si', 'sí', 'no'):
                continue
            txt = 'No' if sel == 'no' else 'Sí'
        else:
            validas = ('local', 'visita', 'empate') if tipo == 'lado3' else ('local', 'visita')
            if sel not in validas:
                continue
            txt = {'local': L, 'visita': V, 'empate': 'Empate'}[sel]
        try:
            prob = float(x.get('prob'))
            prob = round(prob, 3) if 0 <= prob <= 1 else None
        except (TypeError, ValueError):
            prob = None
        out.append({'k': clave, 't': nombre.replace('%L', L).replace('%V', V), 'v': txt, 'p': prob})
    return out or None
