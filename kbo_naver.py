#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v97 — KBO (béisbol coreano): histórico y partidos del día.

Por qué Naver y no otra
-----------------------
Pinnacle cotiza la KBO todos los días («Korea Professional Baseball», medido
el 2026-08-04: 5 partidos con moneyline) y Playdoit también («Liga KBO»), así
que hay mercado. Lo que no había era **resultados** para entrenar. Probado:

  · **statsapi.mlb.com** — tiene la KBO REGISTRADA (`sportId=32`,
    `leagueId=161`, con los 10 equipos y sus ids) pero **0 juegos** en el
    calendario de 2022 a 2026. El catálogo existe; los datos no.
  · **ESPN** — no hay liga de béisbol coreano en su API (`kor.1`, `kbo`,
    `kor.kbo` → HTTP 400).
  · **Naver Sports** (`api-gw.sports.naver.com`) — es ésta. JSON público, sin
    clave, **2008-2026** (18 temporadas), ~720 juegos por temporada, con
    marcador, estadio, **abridor de cada lado** y lanzador ganador. Y llega a
    HOY: el 2026-08-04 los partidos de esa misma tarde ya traían resultado.

Sobre robots.txt: `api-gw.sports.naver.com` no publica ninguno (404, que por
convención es «sin restricciones»); NO se toca `m.sports.naver.com`, que sí
tiene uno restrictivo, ni se parsea su HTML. El histórico completo son ~220
peticiones una sola vez y luego **una al día**.

El esquema de salida es EXACTAMENTE el de `mlb_statsapi` (mismas columnas y
misma semántica), para que `MLBEngine._dataset` —que ya está validado— se
pueda reutilizar tal cual sin tocar una línea del motor de la MLB.
"""

import logging
import os
import time
from typing import Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

API = 'https://api-gw.sports.naver.com/schedule/games'
SALIDA = 'historico_kbo.csv'
CABECERAS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'),
    'Referer': 'https://m.sports.naver.com/',
}
CAMPOS = ('basic,superCategoryId,categoryId,stadium,statusNum,'
          'homeStarterName,awayStarterName,winPitcherName')

# Código de Naver -> nombre canónico en inglés (el que usan Pinnacle, Playdoit
# y statsapi). El código NO cambia cuando la franquicia cambia de patrocinador
# —SK Wyverns pasó a SSG Landers en 2021 y sigue siendo 'SK'—, que es
# justamente lo que mantiene unida la historia del equipo. Es el mismo criterio
# por el que `mlb_statsapi` indexa por id y no por nombre (ver Oakland en v79).
CODIGO_A_EQUIPO: Dict[str, str] = {
    'HH': 'Hanwha Eagles',
    'HT': 'Kia Tigers',
    'KT': 'KT Wiz',
    'LG': 'LG Twins',
    'LT': 'Lotte Giants',
    'NC': 'NC Dinos',
    'OB': 'Doosan Bears',
    'SK': 'SSG Landers',
    'SS': 'Samsung Lions',
    'WO': 'Kiwoom Heroes',
}
EQUIPOS = set(CODIGO_A_EQUIPO.values())

# Estados que cuentan como resultado firme.
FINALES = {'RESULT'}

# Ventaja de campo admisible. En béisbol ronda el 53-54 %; si el reparto
# local/visitante se sale de aquí es que las columnas están cruzadas, y eso
# NO da error: entrena un modelo que predice al revés (lección v96).
LOCAL_MIN, LOCAL_MAX = 0.45, 0.62


# v480 — CORTACIRCUITOS. El 27-oct Naver dejó de responder (sin respuesta en 25-40 s) y cada llamada
# esperaba 40 s × 3 intentos: la app vieja tardaba más de 900 s en pintar la KBO y la suite fallaba.
# Tras un fallo, Naver se da por caído 10 minutos y se va directo a la web oficial de la KBO.
CAIDA_S = 600
_CAIDA = {'hasta': 0.0}
KBO_OFICIAL = 'https://www.koreabaseball.com/ws/Main.asmx/GetKboGameList'
CABECERAS_KBO = {'User-Agent': CABECERAS['User-Agent'],
                 'Referer': 'https://www.koreabaseball.com/Schedule/Schedule.aspx',
                 'X-Requested-With': 'XMLHttpRequest',
                 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}


def _pedir(params: dict, reintentos: int = 2) -> dict:
    if time.time() < _CAIDA['hasta']:
        raise RuntimeError('Naver Sports caído hace menos de %d min: no se reintenta' % (CAIDA_S // 60))
    ultimo = None
    for i in range(reintentos):
        try:
            r = requests.get(API, params=params, headers=CABECERAS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            ultimo = e
            time.sleep(1.5 * (i + 1))
    _CAIDA['hasta'] = time.time() + CAIDA_S
    raise RuntimeError(f'Naver Sports no respondió: {ultimo}')


def _de_kbo_oficial(x: dict) -> dict:
    """Un juego de koreabaseball.com con los campos de Naver que usa `_fila`. El `G_ID` lleva los
    MISMOS códigos de equipo que Naver: «20250920SSLG0» = Samsung (visita) en LG (local), y el
    marcador viene como T (alta: visita) y B (baja: local)."""
    gid = str(x.get('G_ID') or '')
    num = lambda v: int(v) if str(v or '').strip().lstrip('-').isdigit() else None
    return {'gameId': gid, 'gameDate': '%s-%s-%s' % (gid[:4], gid[4:6], gid[6:8]),
            'awayTeamCode': gid[8:10], 'homeTeamCode': gid[10:12],
            'awayTeamScore': num(x.get('T_SCORE_CN')), 'homeTeamScore': num(x.get('B_SCORE_CN')),
            'statusCode': 'RESULT' if str(x.get('GAME_STATE_SC')) == '3' else 'BEFORE',
            'cancel': str(x.get('CANCEL_SC_ID') or '0') not in ('0', ''),
            'awayStarterName': (x.get('T_PIT_P_NM') or '').strip(),
            'homeStarterName': (x.get('B_PIT_P_NM') or '').strip(),
            'stadium': (x.get('S_NM') or '').strip()}


def _juegos_kbo_oficial(desde: str, hasta: str) -> List[dict]:
    """v480 — la web oficial de la KBO, día por día (sólo cuando Naver no responde)."""
    out = []
    for d in pd.date_range(desde, hasta, freq='D'):
        try:
            r = requests.post(KBO_OFICIAL, headers=CABECERAS_KBO, timeout=20,
                              data={'leId': '1', 'srId': '0,1,3,4,5,7,8,9', 'date': d.strftime('%Y%m%d')})
            out += [_de_kbo_oficial(x) for x in (r.json().get('game') or []) if len(str(x.get('G_ID') or '')) >= 12]
        except Exception as e:
            logger.warning(f'[kbo/oficial] {d.date()}: {type(e).__name__}: {e}')
        time.sleep(0.2)
    return out


def _fila(g: dict, solo_finalizados: bool) -> Optional[dict]:
    """Un juego de Naver al esquema de `mlb_statsapi`."""
    if g.get('cancel') or g.get('suspended'):
        return None
    hc = CODIGO_A_EQUIPO.get(g.get('homeTeamCode') or '')
    ac = CODIGO_A_EQUIPO.get(g.get('awayTeamCode') or '')
    if not hc or not ac or hc == ac:
        return None                      # franquicia histórica desaparecida
    if solo_finalizados and g.get('statusCode') not in FINALES:
        return None
    hr, ar = g.get('homeTeamScore'), g.get('awayTeamScore')
    if solo_finalizados and (hr is None or ar is None):
        return None
    return {
        'date': pd.to_datetime(g.get('gameDate'), errors='coerce'),
        'home_team': hc, 'away_team': ac,
        # v104 — EL ID DEL PARTIDO, que venía en la respuesta y se tiraba.
        #
        # Sin él no se puede pedir el box score, y sin box score no hay datos
        # de bullpen: cuántos relevistas usó cada equipo, cuánto trabajaron y
        # con qué efectividad. Ésa es la vía que queda abierta para acercarse
        # al mercado en la KBO, después de que Statiz quedara descartado por su
        # robots.txt (prohíbe explícitamente la recolección automatizada).
        #
        # Es un campo de texto estable (`20260805LGOB02026`) y cuesta cero:
        # ya estaba viajando en el mismo JSON.
        'game_id': (g.get('gameId') or '').strip(),
        # v99.1 — el estadio venía en la respuesta y se tiraba. Es lo que
        # permite calcular el factor de parque: en la KBO el Jamsil de Seúl y
        # el de Daegu no producen las mismas carreras, y el mercado lo
        # descuenta en la línea de totales. Sin este campo no había forma.
        'estadio': (g.get('stadium') or '').strip(),
        'home_runs': int(hr) if hr is not None else None,
        'away_runs': int(ar) if ar is not None else None,
        # El abridor viene por NOMBRE (Naver no da id). Es su espacio de
        # nombres único y estable, igual que los ids de StatsAPI para la MLB.
        'home_pitcher': (g.get('homeStarterName') or '').strip(),
        'away_pitcher': (g.get('awayStarterName') or '').strip(),
    }


def _juegos(desde: str, hasta: str) -> List[dict]:
    try:
        d = _pedir({'fields': CAMPOS, 'upperCategoryId': 'kbaseball',
                    'categoryId': 'kbo', 'fromDate': desde, 'toDate': hasta,
                    'size': 500})
        return (d.get('result') or {}).get('games') or []
    except Exception as e:
        logger.warning(f'[kbo/naver] {e} → web oficial de la KBO')
        return _juegos_kbo_oficial(desde, hasta)


def descargar_temporada(anio: int, solo_finalizados: bool = True) -> pd.DataFrame:
    """
    Temporada completa, pedida MES A MES.

    La API corta en 500 juegos por respuesta y una temporada son ~720, así que
    pedir el año entero devuelve un truncamiento silencioso (medido: 2025
    entero → exactamente 500). Por meses nunca se acerca al tope.
    """
    filas = []
    for mes in range(1, 13):
        ini = f'{anio}-{mes:02d}-01'
        if pd.Timestamp(ini) > pd.Timestamp.today():
            break                        # v482 — los meses que no han llegado no tienen juegos
        fin = (pd.Timestamp(ini) + pd.offsets.MonthEnd(1)).strftime('%Y-%m-%d')
        try:
            crudos = _juegos(ini, fin)
        except Exception as e:
            logger.warning(f'[kbo/naver] {anio}-{mes:02d}: {e}')
            continue
        if len(crudos) >= 500:
            logger.warning(f'[kbo/naver] {anio}-{mes:02d} devolvió {len(crudos)} '
                           f'juegos: posible truncamiento')
        for g in crudos:
            f = _fila(g, solo_finalizados)
            if f is not None:
                filas.append(f)
        time.sleep(0.25)                 # una petición cada 250 ms: educado
    df = pd.DataFrame(filas)
    con_pit = 0
    if not df.empty:
        con_pit = int(((df.home_pitcher != '') & (df.away_pitcher != '')).sum())
    logger.info(f'[kbo/naver] {anio}: {len(df)} juegos ({con_pit} con ambos abridores)')
    return df


def actualizar(anios: List[int], salida: str = SALIDA) -> pd.DataFrame:
    """
    Consolida las temporadas pedidas en `historico_kbo.csv`.

    GUARDIA (regla de oro 7): antes de escribir comprueba que el local gane
    entre el 45 % y el 62 % de las veces. Si `homeTeamCode` y `awayTeamCode`
    estuvieran cruzados —Naver publica un `reversedHomeAway` porque su
    interfaz pinta al visitante a la izquierda— el fichero saldría igual de
    bonito y el modelo aprendería la ventaja de campo con el signo cambiado.
    """
    # v482 — LAS TEMPORADAS CERRADAS NO SE VUELVEN A BAJAR. Se bajaban 2008-hoy en cada
    # reentrenamiento; con Naver caído la web oficial va día por día (~5 min por temporada, ~95 min
    # en total) y el reentrenamiento entero se cortaba por tiempo. Se baja desde la temporada del
    # último juego guardado; lo de antes sale del CSV. Lo bajado se SUMA a lo guardado (gana lo
    # nuevo en el mismo juego): una descarga a medias nunca borra juegos que ya estaban.
    previo = pd.DataFrame()
    if os.path.exists(salida):
        try:
            previo = pd.read_csv(salida, parse_dates=['date'])
            hasta = int(previo['date'].max().year)
            guardadas = set(previo['date'].dt.year.unique())
            anios = [a for a in anios if a >= hasta or a not in guardadas]
        except Exception as e:
            logger.warning(f'[kbo/naver] {salida} ilegible ({e}): se baja todo')
            previo = pd.DataFrame()
    frames = []
    for a in sorted(anios):
        try:
            df = descargar_temporada(a)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            logger.warning(f'[kbo/naver] {a} no disponible: {e}')
    if not frames:
        return pd.read_csv(salida, parse_dates=['date']) \
            if os.path.exists(salida) else pd.DataFrame()

    df = pd.concat(([previo] if not previo.empty else []) + frames, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'home_runs', 'away_runs'])
    df['home_runs'] = df['home_runs'].astype(int)
    df['away_runs'] = df['away_runs'].astype(int)
    df = (df.sort_values('date', kind='stable')        # v482 — estable: en el mismo juego gana lo nuevo
            .drop_duplicates(subset=['date', 'home_team', 'away_team'],
                             keep='last')
            .reset_index(drop=True))

    decididos = df[df.home_runs != df.away_runs]
    pct_local = float((decididos.home_runs > decididos.away_runs).mean()) \
        if len(decididos) else 0.5
    if not (LOCAL_MIN <= pct_local <= LOCAL_MAX):
        raise ValueError(
            f'[kbo/naver] el local gana el {pct_local:.1%} de {len(decididos)} '
            f'juegos decididos, fuera de [{LOCAL_MIN:.0%}, {LOCAL_MAX:.0%}]: '
            f'local y visitante están cruzados. No se escribe {salida}.')

    df.to_csv(salida, index=False)
    logger.info(f"[kbo/naver] {salida}: {len(df)} juegos "
                f"({df['date'].min().date()} → {df['date'].max().date()}) · "
                f"{df['home_team'].nunique()} equipos · "
                f"local gana {pct_local:.1%}")
    return df


def partidos_del_dia(fecha: Optional[str] = None) -> List[dict]:
    """Partidos de hoy CON abridor anunciado, para inferencia."""
    f = fecha or pd.Timestamp.today().strftime('%Y-%m-%d')
    try:
        crudos = _juegos(f, f)
    except Exception as e:
        logger.warning(f'[kbo/naver] partidos del día: {e}')
        return []
    fuera = []
    for g in crudos:
        fila = _fila(g, solo_finalizados=False)
        if not fila:
            continue
        fuera.append({'fecha': f, 'home': fila['home_team'],
                      'away': fila['away_team'],
                      'home_pitcher': fila['home_pitcher'],
                      'away_pitcher': fila['away_pitcher'],
                      'estado': g.get('statusCode')})
    return fuera


def resultados_entre(desde: str, hasta: str) -> List[dict]:
    """Juegos finalizados con marcador, para que el liquidador cierre picks."""
    try:
        crudos = _juegos(desde, hasta)
    except Exception as e:
        logger.warning(f'[kbo/naver] resultados {desde}..{hasta}: {e}')
        return []
    fuera = []
    for g in crudos:
        fila = _fila(g, solo_finalizados=True)
        if not fila:
            continue
        fuera.append({'fecha': str(fila['date'].date()),
                      'home': fila['home_team'], 'away': fila['away_team'],
                      'carreras_home': fila['home_runs'],
                      'carreras_away': fila['away_runs']})
    logger.info(f'[kbo/naver] {len(fuera)} juegos finalizados '
                f'entre {desde} y {hasta}.')
    return fuera


if __name__ == '__main__':
    import argparse
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--desde', type=int, default=2008)
    ap.add_argument('--hasta', type=int, default=pd.Timestamp.today().year)
    a = ap.parse_args()
    d = actualizar(list(range(a.desde, a.hasta + 1)))
    print(json.dumps({'juegos': len(d),
                      'equipos': sorted(d.home_team.unique().tolist()),
                      'desde': str(d.date.min().date()),
                      'hasta': str(d.date.max().date())},
                     ensure_ascii=False, indent=1))
