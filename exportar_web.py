#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v377 — LO QUE VE EL SITIO WEB NUEVO (fuera de Streamlit).

El usuario: «quiero que hagamos eso [una app como BetFlipAi: base de datos +
página web] de manera gratuita». El sitio (carpeta `web/`) no calcula nada:
lee lo que deja este script, igual que la pantalla de Streamlit lee el
precálculo. Mismas funciones que la app (`modo_modelo.lista_por_acierto` y
`lista_finalizadas`), así el sitio y la app dicen lo mismo.

v378 — y a cada pick le pone su partido de ESPN (`espn_vivo`): la página lee
de ahí, cada 30 s, el marcador, el minuto y las estadísticas en vivo.

Escribe `web/datos/hoy.json` y, si hay credenciales de Supabase
(`SUPABASE_URL` y `SUPABASE_SERVICE_KEY`, secretos de GitHub), sube cada pick
a la tabla `picks` (ver `web/supabase.sql`). Sin credenciales sólo escribe el
fichero: nunca falla por eso.

Ejecutar:  python exportar_web.py
"""
import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import sys
from typing import Dict, List, Optional

logger = logging.getLogger('exportar_web')
SALIDA = os.environ.get('WEB_DATOS', os.path.join('web', 'datos', 'hoy.json'))
# v381 — el texto real de los picks premium, para el bot del canal VIP. Fuera
# de `web/` a propósito: lo de `web/` se publica y cualquiera lo leería.
PRIVADO = os.environ.get('WEB_PRIVADO', os.path.join('datos_privados', 'premium.json'))
PRIVADO_VIP = os.path.join(os.path.dirname(PRIVADO) or '.', 'vip.json')        # v482 — jugadores y líneas
# v418 — las tarjetas de «sólo análisis» (partidos sin pick): un fichero APARTE,
# nunca la tabla `picks`, para que no cuenten en verdes/rojas, Telegram ni combinadas
ANALISIS = os.environ.get('WEB_ANALISIS', os.path.join(os.path.dirname(SALIDA), 'analisis.json'))
DIAS_ANALISIS = 3          # hoy, mañana y pasado
# v478 — lo que se publicó en la pasada anterior (para no perder las líneas de la casa al empezar)
PUBLICADO = os.environ.get('SITIO_URL', 'https://sharpicksapp.com').rstrip('/') + '/datos/'
CAMPOS = ('partido', 'inicio', 'fecha', 'deporte', 'liga', 'apuesta', 'cuota', 'prob',
          'elige', 'porque', 'resultado_c1', 'marcador',
          # v378 — para lo en vivo (ver `espn_vivo`)
          'espn', 'logo_h', 'logo_a', 'girado',
          # v379 — el modo de pago (`premium`)
          'premium',
          # v384 — errores de cuota (`errores_web`) y el contexto del partido
          'tipo', 'casa', 'ventaja', 'gratis', 'ctx',
          # v469 — quién puede anotar y tirar a puerta (`jugadores_prob`; columna de supabase/v469_jugadores.sql)
          'jug')


def _id(p: Dict) -> str:
    """El mismo pick siempre con el mismo id (para no duplicarlo al subirlo).

    v505 — sin las marcas ⭐ NI 🏆 (las dos se quitan del texto en `_fila`). Antes sólo se quitaba ⭐: un
    pick que entre pasadas ganaba o perdía el 🏆 tenía dos ids con el mismo texto, y quedaban los dos
    (el usuario: «Plata y Platino tienen el mismo pick»). 28-oct: 192 repetidos desde el 17, contados doble
    en verdes/rojas."""
    k = '|'.join(str(p.get(x) or '') for x in ('fecha', 'partido', 'apuesta'))
    k = k.replace('⭐ ', '').replace('🏆 ', '').encode('utf-8')
    # v508 — CON CLAVE SECRETA (HMAC). El id es público y el sha1 de «fecha|partido|apuesta» se deshacía
    # probando las apuestas posibles del partido: en la auditoría del 28-oct salieron 40 de 40 picks de pago
    # («🔒 Pick Diamante») sólo con su id. Sin la clave (`PICK_ID_CLAVE`, secreto de GitHub) no se puede.
    clave = os.environ.get('PICK_ID_CLAVE', '')
    if clave:
        return hmac.new(clave.encode('utf-8'), k, hashlib.sha1).hexdigest()[:20]
    if os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('SUPABASE_SERVICE_KEY'):
        raise RuntimeError('falta PICK_ID_CLAVE: sin ella los ids dejarían ver los picks de pago')
    return hashlib.sha1(k).hexdigest()[:20]          # sólo local y pruebas (nunca se publica así)


def _fila(p: Dict, estado: str, ligas: Dict = None) -> Dict:
    f = {k: p.get(k) for k in CAMPOS}
    if not f.get('liga') and ligas:
        f['liga'] = ligas.get(p.get('partido'))
    f['apuesta'] = str(f.get('apuesta') or '').replace('⭐ ', '').replace('🏆 ', '')
    f['estado'] = estado
    # v389 — la hora, siempre como fecha (nunca segundos sueltos ni texto raro):
    # un solo pick así hacía que Supabase rechazara el lote entero
    ini = str(f.get('inicio') or '').strip()
    if ini.replace('.', '', 1).isdigit():
        try:
            ini = dt.datetime.fromtimestamp(float(ini), dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ini = ''
    f['inicio'] = ini if len(ini) >= 10 and ini[:4].isdigit() and ini[4] == '-' else None
    # la tabla exige la fecha: sin ella, Supabase rechazaría el lote entero
    f['fecha'] = f.get('fecha') or str(f.get('inicio') or '')[:10] or None
    f['id'] = _id(p)
    f['elige'] = bool(f.get('elige'))
    f['gratis'] = bool(f.get('gratis'))
    f['tipo'] = f.get('tipo') or 'pick'
    for k in ('cuota', 'prob', 'ventaja'):
        try:
            f[k] = round(float(f[k]), 3) if f.get(k) is not None else None
        except (TypeError, ValueError):
            f[k] = None
    try:
        import nombres_ligas
        if f.get('liga'):
            f['liga'] = nombres_ligas.canonica(f['liga'], p.get('clave_liga') or '',
                                               f.get('deporte') or '')
    except Exception:
        pass
    return f


def decidir_lo_que_falta(datos: Dict) -> int:
    """v406 — LAS DECISIONES QUE FALTAN SE CALCULAN AQUÍ.

    El usuario: «cuando quise ver los partidos de mañana y pasado mañana me
    salían vacíos». Las «se mete» las calcula el precálculo y viajan con una
    huella de los ficheros que usó (`decisiones_dia`); si un bot commitea uno
    de esos ficheros después (las cuotas, cada hora) o pasa la medianoche UTC,
    `adjuntar` las descarta («se calculan en vivo»)… pero `lista_por_acierto`
    NUNCA las calculaba en vivo: sólo lee las guardadas. Medido el 20-oct: la
    pasada sin decisiones bajaba de 549 picks a 307 (y a 187), y la limpieza
    de lo retirado borraba los de mañana y pasado.

    Aquí se calculan con la MISMA función del cron (`decisiones_dia.decidir`)
    para cada partido sin jugar que no la trae. Devuelve cuántos."""
    import decisiones_dia as dd
    faltan = [p for lista in dd.LISTAS for p in (datos.get(lista) or [])
              if isinstance(p, dict) and not p.get('jugado') and dd.CLAVE_PICK not in p]
    if not faltan:
        return 0
    try:                         # el cron decide con los nombres de liga ya unificados
        import nombres_ligas
        nombres_ligas.aplicar(datos)
    except Exception as e:
        logger.debug('[web] nombres de liga: %s', e)
    n = 0
    for p in faltan:
        try:
            p[dd.CLAVE_PICK] = {'llave': dd._llave(p), **dd.decidir(p)}
            n += 1
        except Exception as e:
            logger.debug('[web] decisión de %s: %s', p.get('partido'), e)
    logger.info('[web] %d decisiones calculadas aquí (las del precálculo no valían)', n)
    return n


def _dia_mx(f: Dict) -> str:
    """v466 — el día en México de la hora de inicio, que es como la página arma «Hoy / Mañana /
    Pasado». `fecha` sale de la hora en UTC: Tigres-Monterrey a las 18:06 del 25 decía «26» y se
    quedaba fuera de «Pasado» (y así cualquier partido sin pick desde las 18:00)."""
    try:
        i = dt.datetime.fromisoformat(str(f.get('inicio')).replace(' ', 'T').replace('Z', '+00:00'))
        i = i if i.tzinfo else i.replace(tzinfo=dt.timezone.utc)
        return i.astimezone(dt.timezone(dt.timedelta(hours=-6))).date().isoformat()
    except Exception:
        return str(f.get('fecha'))


def solo_analisis(prons: List[Dict], picks: List[Dict], terminados: List[Dict], hoy: dt.date) -> List[Dict]:
    """v418 — «quiero que me salgan TODOS los partidos con su tarjeta para
    analizarlos, con la sugerencia del modelo, la IA y las estadísticas; los
    que no tengan recomendación, que digan sutil que es sólo análisis».

    Napoli vs Bodø y Sabah vs Dortmund no salían: el modelo los evaluó (y la
    casa los cotizaba) pero ningún pick pasó los filtros. Aquí sale una fila
    por cada partido SIN pick: los que vienen (hoy, mañana y pasado) y los ya
    jugados de hoy y ayer, con la sugerencia del modelo como dato, no como pick.
    """
    con_pick = {(str(f.get('fecha')), str(f.get('partido'))) for f in picks}
    limite = (hoy + dt.timedelta(days=DIAS_ANALISIS - 1)).isoformat()
    out, vistos = [], set()
    filas = [(x, 'pendiente') for x in prons if not x.get('jugado') and not x.get('sigue')] + [(x, 'final') for x in terminados]
    for p, est in filas:
        if est == 'final' and not p.get('marcador'):
            gh, ga = p.get('goles_home'), p.get('goles_away')
            if gh is None or ga is None:
                continue
            p = dict(p, marcador='%s-%s' % (gh, ga))
        try:
            f = _fila(p, est)
        except Exception:
            continue
        k = (str(f.get('fecha')), str(f.get('partido')))
        if not f.get('fecha') or ' vs ' not in str(f.get('partido') or '') and ' @ ' not in str(f.get('partido') or '') \
                and ' - ' not in str(f.get('partido') or '') and ' – ' not in str(f.get('partido') or ''):
            continue
        if k in con_pick or k in vistos or (est == 'pendiente' and not (hoy.isoformat() <= _dia_mx(f) <= limite)):
            continue
        vistos.add(k)
        f.update(solo_analisis=True, tipo='analisis', premium=False, elige=False, cuota=None, gratis=True)
        f['id'] = 'an-' + f['id']
        out.append(f)
    return out


# v423 — EL BÉISBOL DE INVIERNO, SÓLO ANÁLISIS. Las casas mexicanas cotizan la
# Liga Mexicana del Pacífico, la dominicana y la venezolana, que el sistema no
# tenía. MEDIDO (3.406 partidos 2021-2026 con la cuota de cierre de
# Betexplorer): la casa SOBREVALORA al favorito —en 60-65 % ganó 51,8 %; con
# 65 %+ gana 64,3 % (p5 57,7 %, 2.ª mitad 60 %) y deja −11 por cada $100— y
# casi no hay favoritos de 70 %+ (21 en cinco temporadas). No hay pick que
# vender: salen como tarjetas de «sólo análisis» con lo que ve la casa y la IA.
BEISBOL_INVIERNO = {'MEXICO: LMP': 'Liga Mexicana del Pacífico',
                    'DOMINICAN REPUBLIC: LIDOM': 'Liga Dominicana (LIDOM)',
                    'VENEZUELA: LVBP': 'Liga Venezolana (LVBP)'}


def beisbol_invierno(hoy: dt.date, ruta: str = 'cuotas_mx.json') -> List[Dict]:
    try:
        d = json.load(open(ruta, encoding='utf-8'))
    except Exception:
        return []
    ps = d.get('partidos') or []
    ps = ps if isinstance(ps, list) else list(ps.values())
    cdmx = dt.timezone(dt.timedelta(hours=-6))
    out = []
    for p in ps:
        liga = BEISBOL_INVIERNO.get(str(p.get('liga') or '').split(' - ')[0])
        if not liga or not p.get('home') or not p.get('away'):
            continue
        try:
            ini = dt.datetime.fromtimestamp(float(p['inicio']), dt.timezone.utc)
        except Exception:
            continue
        if not (hoy <= ini.astimezone(cdmx).date() <= hoy + dt.timedelta(days=DIAS_ANALISIS - 1)):
            continue
        ih, ia = [], []
        for casa in (p.get('casas') or {}).values():
            ml = (casa or {}).get('HOME_AWAY') or {}
            try:
                ih.append(1 / float(ml['home'])); ia.append(1 / float(ml['away']))
            except Exception:
                continue
        if not ih:
            continue
        h, a = sum(ih) / len(ih), sum(ia) / len(ia)
        ph = h / (h + a)
        fav, prob = (p['home'], ph) if ph >= 0.5 else (p['away'], 1 - ph)
        f = _fila({'partido': '%s vs %s' % (p['home'], p['away']), 'deporte': 'Béisbol', 'liga': liga,
                   'inicio': ini.strftime('%Y-%m-%d %H:%M:%S'), 'fecha': ini.astimezone(cdmx).date().isoformat(),
                   'apuesta': 'Gana %s' % fav, 'prob': prob}, 'pendiente')
        f.update(solo_analisis=True, tipo='analisis', premium=False, elige=False, cuota=None, gratis=True, fuente='casa')
        f['id'] = 'an-' + f['id']
        out.append(f)
    return out


def _lin_publicadas() -> Dict:
    """v478 — las líneas CON CASA de la pasada anterior, por (fecha, partido). Al empezar el partido
    Playdoit lo saca de su catálogo pre-partido y la pasada siguiente ya no lo encuentra: sin esto, el
    parley y las líneas de la casa desaparecían justo cuando el partido está en vivo.
    v482 — las líneas ya no van en lo público: se leen de `picks_vip` con la clave de servicio."""
    import requests
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return {}
    out = {}
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).strftime('%Y-%m-%d')
    for i in range(0, 20000, 1000):                      # v466 — la base entrega 1000 por consulta
        try:
            r = requests.get(url.rstrip('/') + '/rest/v1/picks_vip', timeout=30,
                             headers={'apikey': key, 'Authorization': 'Bearer ' + key},
                             params={'select': 'fecha,partido,lin', 'fecha': 'gte.' + desde,
                                     'order': 'clave', 'limit': 1000, 'offset': i})
            filas = r.json() if r.ok else []
        except Exception as e:
            logger.warning('[web] sin las líneas publicadas: %s', e)
            break
        for f in filas:
            lin = f.get('lin') or {}
            if lin.get('casa') and f.get('partido'):
                out.setdefault((str(f.get('fecha')), f['partido']), lin)
        if len(filas) < 1000:
            break
    return out


def separar_vip(filas: List[Dict]) -> Dict[str, Dict]:
    """v482 — LO DEL VIP SALE DE LO PÚBLICO. Los jugadores (`jug`) y las líneas por estadística
    (`ctx.lin`, con el parley) viajaban en `hoy.json`, `analisis.json` y la tabla `picks`, que lee
    cualquiera: la página los tapaba, pero se veían con las herramientas del navegador. Se quitan de
    cada fila (queda `vip_hay` para el 🔒) y se devuelven por partido para `picks_vip`, que la base
    sólo deja leer al VIP (`es_pro()`)."""
    vip = {}
    for f in filas:
        ctx = f.get('ctx') or {}
        jug, lin = f.get('jug'), ctx.get('lin')
        if f.get('partido') and (jug or lin):
            v = vip.setdefault('%s|%s' % (f.get('fecha'), f['partido']),
                               {'clave': '%s|%s' % (f.get('fecha'), f['partido']), 'fecha': f.get('fecha'),
                                'partido': f['partido'], 'jug': None, 'lin': None})
            v['jug'] = v['jug'] or jug
            v['lin'] = v['lin'] or lin
        f['vip_hay'] = bool(jug or lin)
        f['jug'] = None
        if 'lin' in ctx:
            f['ctx'] = {k: x for k, x in ctx.items() if k != 'lin'}   # copia: el ctx se comparte entre picks
    return vip


def subir_vip(vip: Dict[str, Dict]) -> int:
    """v482 — sube los jugadores y las líneas de cada partido a `picks_vip` y borra lo de hace más
    de 5 días. Si la base lo rechaza, no se publica (el VIP se quedaría sin su análisis)."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key or not vip:
        return 0
    import requests
    hdr = {'apikey': key, 'Authorization': 'Bearer ' + key,
           'Prefer': 'resolution=merge-duplicates,return=minimal'}
    ahora = dt.datetime.now(dt.timezone.utc).isoformat()
    filas = [dict(v, actualizado=ahora) for v in vip.values()]
    for i in range(0, len(filas), 200):
        r = requests.post(url.rstrip('/') + '/rest/v1/picks_vip', json=filas[i:i + 200], timeout=30, headers=hdr)
        if not r.ok:
            logger.error('[web] picks_vip: %s %s', r.status_code, r.text[:200])
            raise RuntimeError('No se pudo guardar lo del VIP en Supabase; se bloquea la publicación')
    viejo = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=5)).strftime('%Y-%m-%d')
    requests.delete(url.rstrip('/') + '/rest/v1/picks_vip', timeout=30, headers=hdr, params={'fecha': 'lt.' + viejo})
    return len(filas)


def _ya_empezo(f: Dict, ahora: dt.datetime) -> bool:
    try:
        ini = dt.datetime.strptime(str(f.get('inicio'))[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return False
    return ini <= ahora


def conservar_lin_casa(filas: List[Dict], previas: Dict, ahora: dt.datetime = None) -> int:
    """v478 — al partido que ya empezó y esta pasada dejó sin casa, se le devuelve el `lin` con casa
    de la pasada anterior. Devuelve cuántos se conservaron."""
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    n = 0
    for f in filas:
        if f.get('deporte') != 'Fútbol' or not _ya_empezo(f, ahora):
            continue
        if ((f.get('ctx') or {}).get('lin') or {}).get('casa'):
            continue
        lin = previas.get((f.get('fecha'), f.get('partido')))
        if lin:
            f['ctx'] = dict(f.get('ctx') or {}, lin=lin)      # copia: el ctx se comparte entre picks del partido
            n += 1
    return n


def _ligas_solo_analisis() -> Dict[str, str]:
    """v479 — {clave: nombre} de las competiciones que están en el modelo y en la página como ANÁLISIS
    (tarjeta, líneas de la casa, parley, IA) pero cuyos picks todavía no cuentan (verdes/rojas, Telegram,
    combinadas): `solo_analisis` en su configuración. Hoy la DFB-Pokal y la Copa del Rey, hasta medirlas
    al nivel de las ligas (simulado: la Copa del Rey da 75,9 % a los 90' contra el 82 % del historial)."""
    try:
        import config
        return {c: str(cfg.get('nombre') or c) for c, cfg in config.LEAGUES.items() if cfg.get('solo_analisis')}
    except Exception:
        return {}


def _cuenta(p: Dict, solo: Dict[str, str]) -> bool:
    return not (p.get('clave_liga') in solo or str(p.get('liga') or '') in solo.values())


def sugerencia_de_la_casa(filas: List[Dict], solo: Dict[str, str], claves: Dict = None) -> int:
    """v480 — EN LAS COPAS LA SUGERENCIA DE LA TARJETA ES LA DE LA CASA, NO LA DEL MODELO.

    El modelo no conoce a los equipos amateur y los trata como de nivel medio con localía: la tarjeta
    decía «Gana CD Minera 59 %» contra el Cartagena y «Gana AE Prat» contra el Athletic. Simulado
    (cierres de BetExplorer, 1X2 a 90'): la casa 0,766 / 0,853 de log-loss contra 0,822 / 0,949 del
    mejor ELO (Pokal / Copa del Rey). Sin precio de la casa, la tarjeta se queda sin sugerencia."""
    import errores_web
    n = 0
    for f in filas:
        if f.get('deporte') != 'Fútbol' or _cuenta(f, solo) or ' vs ' not in str(f.get('partido') or ''):
            continue
        h, a = [s.strip() for s in str(f['partido']).split(' vs ', 1)]
        try:
            x = (errores_web.casa_del_partido(h, a, (claves or {}).get(f['partido']), f.get('inicio'), f.get('liga') or '') or {}).get('1x2') or {}
        except Exception:
            x = {}
        if x.get('home') and x.get('away'):
            lado = 'home' if float(x['home']) >= float(x['away']) else 'away'
            f.update(apuesta='Gana %s' % (h if lado == 'home' else a), prob=round(float(x[lado]), 3), fuente='casa')
            n += 1
        else:
            f.update(apuesta='', prob=None)
    return n


def construir() -> Dict:
    import modo_modelo as mm
    import partidos_jugados as pj
    import precalculo_dia as pc
    doc = pc.leer() or {}
    decidir_lo_que_falta(doc.get('datos') or {})
    prons = (doc.get('datos') or {}).get('pronosticos') or []
    solo = _ligas_solo_analisis()
    proximas = [f for f in (_fila(p, 'pendiente') for p in mm.lista_por_acierto(prons)
                            if not p.get('sigue') and _cuenta(p, solo)) if _cuenta(f, solo)]   # v504
    jugadas, terminados = [], []
    hoy = dt.datetime.now(dt.timezone(dt.timedelta(hours=-6))).date()
    for d in (hoy - dt.timedelta(days=1), hoy):
        lst = pj._para_la_vista(pj._leer_precalculo(d.isoformat(), permitir_viejo=True) or [])
        terminados += [x for x in lst if x.get('jugado')]
        ligas = {x.get('partido'): x.get('liga') for x in lst}
        # v504 — el filtro de las copas se aplica a la FILA ya hecha (con su liga). Antes se aplicaba al
        # partido de `lista_finalizadas`, que llega sin liga (la pone `_fila`): todo pick de copa que
        # empezaba entraba por aquí y contaba (28-oct: 17 de la Pokal y la Copa del Rey).
        jugadas += [f for f in (_fila(p, {'verde': 'verde', 'rojo': 'roja', 'nula': 'nula'}.get(
            p.get('resultado_c1'), 'vivo'), ligas) for p in mm.lista_finalizadas(lst)) if _cuenta(f, solo)]
    # v384 — los errores de cuota (💰 «Cuota alta»): ver `errores_web`
    errs = []
    try:
        import errores_web
        errs = [f for f in (_fila(e, e['estado']) for e in errores_web.errores(doc.get('datos') or {}) if _cuenta(e, solo)) if _cuenta(f, solo)]   # v504
    except Exception as e:
        logger.warning('[web] sin errores de cuota: %s', e)
    vistos, picks = set(), []
    for f in [x for x in jugadas + proximas + errs if x.get('fecha')]:          # lo jugado manda sobre lo pendiente
        if f['id'] not in vistos:
            vistos.add(f['id'])
            picks.append(f)
    analisis = []
    try:
        analisis = solo_analisis(prons, picks, terminados, hoy)
        ya = {(a['fecha'], a['partido']) for a in analisis}
        analisis += [b for b in beisbol_invierno(hoy) if (b['fecha'], b['partido']) not in ya]   # v423
    except Exception as e:
        logger.warning('[web] sin tarjetas de sólo análisis: %s', e)
    # v384 — el contexto (forma, H2H, bajas) de cada partido de fútbol. v464 — TAMBIÉN de los que ya
    # empezaron o terminaron (el usuario los veía en vivo sin estadísticas: sólo se hacía a los pendientes)
    try:
        import errores_web
        errores_web.RED_CASA = True       # v477 — lo que no esté en mercado_dia.json se pide a Playdoit en vivo
        memo = {}
        claves = {p.get('partido'): p.get('clave_liga') for p in prons if p.get('clave_liga')}
        for f in picks + analisis:
            if f.get('deporte') == 'Fútbol':
                k = f.get('partido')
                if k not in memo:
                    memo[k] = errores_web.contexto(dict(f, clave_liga=f.get('clave_liga') or claves.get(k)))
                if memo[k]:
                    f['ctx'] = memo[k]
        print('web: líneas de la casa conservadas al empezar: %d' % conservar_lin_casa(picks + analisis, _lin_publicadas()))
        print('web: copas con la sugerencia de la casa: %d' % sugerencia_de_la_casa(analisis, solo, claves))
    except Exception as e:
        logger.warning('[web] sin contexto: %s', e)
    # v492 — la tabla de clasificación de cada liga con partido hoy (ESPN), para la pestaña «Clasificación»
    try:
        import tablas_web
        claves_t = {p.get('partido'): p.get('clave_liga') for p in prons if p.get('clave_liga')}
        print('web: tablas de clasificación: %d ligas' % tablas_web.escribir(tablas_web.generar(picks + analisis, claves_t),
                                                                          os.path.join(os.path.dirname(SALIDA) or '.', 'tablas.json')))
    except Exception as e:
        logger.warning('[web] sin tablas de clasificación: %s', e)
    # v378 — el partido de ESPN de cada pick (marcador y estadísticas en vivo)
    try:
        import espn_vivo
        crudos = {f['id']: f for f in picks + analisis}
        espn_vivo.emparejar(list(crudos.values()))
        for f in picks + analisis:
            f['girado'] = bool(f.get('girado'))
    except Exception as e:
        logger.warning('[web] sin ESPN: %s', e)
    # v467 — cada escudo validado uno por uno; los que faltan, de FotMob/Flashscore (fútbol) y
    # 365Scores (la foto del tenista)
    try:
        import escudos
        st = escudos.poner(picks + analisis)
        logger.info('[web] escudos: %s', st)
        print('web: escudos %s' % st)
    except Exception as e:
        logger.warning('[web] sin escudos: %s', e)
    # v469 — qué jugador puede anotar y tirar a puerta 1+/2+ (medido y calibrado; va en el análisis IA)
    try:
        import jugadores_prob
        print('web: jugadores en %d partidos' % jugadores_prob.poner(picks + analisis))
    except Exception as e:
        logger.warning('[web] sin jugadores: %s', e)
    return {'generado': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'precalculo': doc.get('generado'), 'picks': picks, 'analisis': analisis}


def nivel(p: Dict) -> str:
    """El mismo nivel que la página (`web/app.js`) y Telegram (`telegram_canales`)."""
    if p.get('tipo') == 'error':
        return 'Cuota alta'
    if p.get('elige'):
        return 'Diamante'
    # v545 — 🥇 Oro = más cuota, menos probabilidad (70-79 % y cuota ≥ 1,25; medido 75 % a 1,27); 🔷 Platino ≥ 80 %
    pr, cu = float(p.get('prob') or 0), float(p.get('cuota') or 0)
    return 'Platino' if pr >= 0.80 else ('Oro' if pr >= 0.70 and cu >= 1.25 else 'Plata')


# v547 — SIN PICKS DE REGALO. El usuario (30-oct): «mejor quita los picks de regalo». Lo gratis es el 🥇 Oro
# (70-79 % y cuota ≥ 1,25, v545) y las 20 monedas al crear la cuenta. Los regalos de v544-v545 vuelven a ser
# de pago en la siguiente pasada (su `gratis` ya no se pone).


def premium(picks: List[Dict]) -> List[Dict]:
    """v379 — EL MODO DE PAGO (apagado en el lanzamiento: todo gratis).

    Con `PREMIUM_NIVELES` (p. ej. «Diamante»), el texto de esos picks que aún
    no empiezan SALE de lo público (el fichero de la página y la tabla
    `picks`, que lee cualquiera) y va sólo a `picks_premium`, que la base deja
    leer a quien lo desbloqueó o es Pro (`web/negocio.sql`). Esconderlo en la
    página no serviría: el fichero se ve en el navegador. Devuelve las filas
    para `picks_premium`."""
    nv = {x.strip().capitalize() for x in os.environ.get('PREMIUM_NIVELES', '').split(',') if x.strip()}
    secretos = []
    for p in picks:
        # v384 — lo que va al canal gratis es muestra: no se tapa
        p['premium'] = bool(nv) and nivel(p) in nv and p.get('estado') in ('pendiente', 'vivo') and not p.get('gratis')
        if p['premium']:
            secretos.append({'id': p['id'], 'apuesta': p['apuesta']})
            p['apuesta'] = '🔒 Pick %s' % nivel(p)
    return secretos


CAIDA_MAXIMA_FUTUROS = 0.30


def _pasada_incompleta(url: str, key: str, picks: List[Dict]) -> bool:
    """v406 — ¿esta pasada trae MUCHOS menos picks futuros que la base? Entonces
    no se borra nada: lo más probable es que le falten decisiones o datos, no que
    el modelo haya retirado de golpe un tercio de todo. Se borra en la siguiente
    pasada sana."""
    import requests
    ahora = dt.datetime.now(dt.timezone.utc)
    futuros = 0
    for p in picks:
        try:
            ini = dt.datetime.fromisoformat(str(p.get('inicio')).replace(' ', 'T').replace('Z', '+00:00'))
            ini = ini if ini.tzinfo else ini.replace(tzinfo=dt.timezone.utc)
        except Exception:
            continue
        futuros += p.get('estado') == 'pendiente' and ini > ahora
    try:
        r = requests.get(url.rstrip('/') + '/rest/v1/picks', timeout=30,
                         headers={'apikey': key, 'Authorization': 'Bearer ' + key,
                                  'Prefer': 'count=exact', 'Range': '0-0'},
                         params={'select': 'id', 'estado': 'eq.pendiente',
                                 'inicio': 'gt.' + ahora.strftime('%Y-%m-%dT%H:%M:%S')})
        total = int(str(r.headers.get('content-range', '*/0')).split('/')[-1])
    except Exception as e:
        logger.warning('[web] no se pudo contar lo publicado: %s', e)
        return True                         # sin saberlo, no se borra
    if total and futuros < (1 - CAIDA_MAXIMA_FUTUROS) * total:
        logger.warning('[web] esta pasada trae %d picks futuros y la base tiene %d: NO se borra lo retirado',
                       futuros, total)
        return True
    return False


def _patas_fijas(url: str, key: str) -> Optional[set]:
    """v491 — LAS PATAS DE UNA COMBINADA FIJA NO SE BORRAN. El usuario: «me sale Pick Platino y no me deja
    ir al partido, pero soy VIP». Una combinada queda fija en cuanto empieza su primera pata o alguien la
    compra (`combinadas_web.subir`), pero sus otras patas podían retirarse después (el modelo dejaba de
    meterlas) y el borrado de lo retirado se las llevaba con su texto premium: la pata quedaba «🔒 Pick
    Platino» para todos, sin poder abrirse y sin liquidarse nunca. Devuelve los ids a conservar; None si
    no se pudo saber (entonces no se borra nada)."""
    import requests
    hdr = {'apikey': key, 'Authorization': 'Bearer ' + key}
    base = url.rstrip('/') + '/rest/v1/'
    desde = (dt.datetime.now(dt.timezone(dt.timedelta(hours=-6))).date() - dt.timedelta(days=2)).isoformat()
    try:
        r = requests.get(base + 'combinadas', headers=hdr, timeout=30,
                         params={'select': 'id,patas', 'fecha': 'gte.' + desde, 'limit': 2000})
        rp = requests.get(base + 'desbloqueos_combinada', headers=hdr, timeout=30,
                          params={'select': 'combinada', 'limit': 10000})
        if not r.ok or not rp.ok:
            logger.warning('[web] sin combinadas (%s/%s): no se borra lo retirado en esta pasada', r.status_code, rp.status_code)
            return None
        pagadas = {x['combinada'] for x in rp.json()}
        ahora = dt.datetime.now(dt.timezone.utc)

        def empezo(x):
            try:
                d = dt.datetime.fromisoformat(str(x.get('inicio')).replace('Z', '+00:00'))
                return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)) <= ahora
            except (TypeError, ValueError):
                return False
        out = set()
        for c in r.json():
            pt = c.get('patas') or []
            if c['id'] in pagadas or any(empezo(x) for x in pt):
                out |= {x['id'] for x in pt if x.get('id')}
        # v550 — el usuario: «en las combinadas que había metido se ven patas en blanco, sin descripción del partido». El
        # borrado de lo retirado se llevaba también los picks que la gente ya usó: las patas de SUS combinadas (que
        # entonces se liquidaban sin ellas y perdían el premio), lo que sigue y lo que desbloqueó con monedas (que ya no
        # se devolvían si salía roja). Esos se quedan; se liquidan como cualquier otro (`liquidar_pendientes`).
        ru = requests.get(base + 'combinadas_usuario', headers=hdr, timeout=30,
                          params={'select': 'patas', 'estado': 'eq.pendiente', 'limit': 10000})
        rs = requests.get(base + 'seguidos', headers=hdr, timeout=30, params={'select': 'pick', 'limit': 50000})
        rd = requests.get(base + 'desbloqueos', headers=hdr, timeout=30, params={'select': 'pick', 'limit': 50000})
        # y el usuario: «si mandas un pick se tiene que quedar con eso»: lo que ya salió por Telegram tampoco se retira
        rt = requests.get(base + 'telegram_enviados', headers=hdr, timeout=30, params={'select': 'pick', 'tipo': 'eq.pick', 'limit': 50000})
        if not ru.ok or not rs.ok or not rd.ok or not rt.ok:
            logger.warning('[web] sin lo que usan los usuarios (%s/%s/%s/%s): no se borra lo retirado en esta pasada',
                           ru.status_code, rs.status_code, rd.status_code, rt.status_code)
            return None
        for c in ru.json():
            out |= set(c.get('patas') or [])
        out |= {x['pick'] for x in rs.json() + rd.json() + rt.json() if x.get('pick')}
        return out
    except Exception as e:
        logger.warning('[web] sin combinadas (%s): no se borra lo retirado en esta pasada', e)
        return None


def subir_supabase(picks: List[Dict], secretos: List[Dict] = ()) -> int:
    """Sube (o actualiza) cada pick en Supabase. Devuelve cuántos; 0 sin claves."""
    url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        if secretos:
            raise RuntimeError('Hay picks premium por publicar pero faltan SUPABASE_URL/SUPABASE_SERVICE_KEY')
        return 0
    if not picks:
        return 0
    import requests
    filas = [dict(p, actualizado=dt.datetime.now(dt.timezone.utc).isoformat()) for p in picks]
    # v384 — un error de cuota deja de salir en la Capa 1 al empezar su partido:
    # su verde o roja se toma de lo anunciado y se pone a la fila que ya está
    try:
        import errores_web
        res = errores_web._resultados_anunciados()
        ya = {p['id'] for p in picks}
        r0 = requests.get(url.rstrip('/') + '/rest/v1/picks', timeout=30,
                          headers={'apikey': key, 'Authorization': 'Bearer ' + key},
                          params={'select': '*', 'tipo': 'eq.error', 'estado': 'eq.pendiente',
                                  'inicio': 'lt.' + dt.datetime.now(dt.timezone.utc).isoformat()})
        for x in (r0.json() if r0.ok else []):
            rr = res.get((x.get('partido'), x.get('apuesta')))
            if rr and x['id'] not in ya:
                x.update(estado={'verde': 'verde', 'rojo': 'roja'}.get(rr[0], 'pendiente'), marcador=rr[1],
                         actualizado=dt.datetime.now(dt.timezone.utc).isoformat())
                filas.append({k: x.get(k) for k in filas[0]} if filas else x)
    except Exception as e:
        logger.warning('[web] errores ya jugados: %s', e)
    n = 0
    fallos_filas = []
    hdr = {'apikey': key, 'Authorization': 'Bearer ' + key,
           'Prefer': 'resolution=merge-duplicates,return=minimal'}
    for i in range(0, len(filas), 200):
        r = requests.post(url.rstrip('/') + '/rest/v1/picks', json=filas[i:i + 200], timeout=30,
                          headers=hdr)
        if r.ok:
            n += len(filas[i:i + 200])
        else:
            logger.warning('[web] Supabase respondió %s: %s', r.status_code, r.text[:200])
            # v389 — si el lote falla, uno por uno: que un pick malo no tire a los otros 199
            for fila1 in filas[i:i + 200]:
                r1 = requests.post(url.rstrip('/') + '/rest/v1/picks', json=[fila1], timeout=30, headers=hdr)
                if r1.ok:
                    n += 1
                else:
                    fallos_filas.append(fila1.get('id'))
    # v379 — LO RETIRADO SE BORRA. Si el modelo cambia «Menos de 3.5» por
    # «Menos de 4.5», la vieja se quedaba «pendiente» en la base para siempre y
    # el partido salía dos veces. Se borran las pendientes de partidos que aún
    # no empiezan y que ya no están en esta pasada (sólo si la pasada trae
    # picks: una vacía por un fallo no debe vaciar la base).
    fijas = _patas_fijas(url, key)
    if n == len(filas) and filas and fijas is not None and not _pasada_incompleta(url, key, picks):
        ahora = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        # v554 — la lista «not.in» con todo lo protegido (v550: también claves «comb:a+b» de Telegram) rompía la URL (400).
        # Ahora se piden los pendientes futuros, se calcula aquí qué sobra y se borra por id, en tandas.
        vivos = {p['id'] for p in picks} | fijas
        rr = requests.get(url.rstrip('/') + '/rest/v1/picks', timeout=30, headers=hdr,
                          params={'select': 'id', 'estado': 'eq.pendiente', 'inicio': 'gt.' + ahora, 'limit': 10000})
        sobra = [x['id'] for x in (rr.json() if rr.ok else []) if x['id'] not in vivos]
        r = rr
        for i in range(0, len(sobra), 100):
            r = requests.delete(url.rstrip('/') + '/rest/v1/picks', timeout=30, headers=hdr,
                                params={'estado': 'eq.pendiente', 'id': 'in.(%s)' % ','.join(sobra[i:i + 100])})
            if not r.ok:
                break
        if not r.ok:
            logger.error('[web] no se pudo limpiar lo retirado: %s %s', r.status_code, r.text[:200])
            raise RuntimeError('Supabase no pudo limpiar picks retirados; se bloquea la publicación')
    if fallos_filas:
        logger.error('[web] no se sincronizaron %d picks: %s', len(fallos_filas), ','.join(str(x) for x in fallos_filas[:10]))
        raise RuntimeError('Supabase rechazó %d picks incluso tras reintentar uno por uno' % len(fallos_filas))
    if secretos:
        r = requests.post(url.rstrip('/') + '/rest/v1/picks_premium', json=list(secretos), timeout=30,
                          headers=hdr)
        if not r.ok:
            logger.error('[web] picks premium: %s %s', r.status_code, r.text[:200])
            raise RuntimeError('No se pudo guardar el texto premium en Supabase; se bloquea la publicación')
    return n


FINALES = ('verde', 'roja', 'nula')


def no_retroceder(picks: List[Dict], url: str = None, key: str = None, base: Dict = None) -> int:
    """v510 — UN PICK LIQUIDADO NUNCA VUELVE A «POR JUGAR».

    El usuario: «en el historial me estás dando menos acertadas que en la página principal». Medido el
    29-oct: el 27 tenía 178 ✅ 32 ❌ y 47 por jugar; dos pasadas después, 175 ✅ 30 ❌ y 52. `liquidar_pendientes`
    cierra en la base los tenis que el cálculo del día no sabe (ITF, por la ficha del jugador), y la pasada
    siguiente los volvía a subir «vivo» (su cálculo sigue sin el resultado) y pisaba el verde o el rojo.
    Aquí, antes de subir: si la base ya tiene ese id en verde/roja/nula y esta pasada lo trae sin final, se
    queda el de la base. Devuelve cuántos. `base` ({id: fila}) es para las pruebas, sin red."""
    abiertos = [p for p in picks if p.get('id') and p.get('estado') not in FINALES]
    if not abiertos:
        return 0
    if base is None:
        url = url or os.environ.get('SUPABASE_URL', '')
        key = key or os.environ.get('SUPABASE_SERVICE_KEY', '')
        if not url or not key:
            return 0
        import requests
        base = {}
        hdr = {'apikey': key, 'Authorization': 'Bearer ' + key}
        ids = [p['id'] for p in abiertos]
        for i in range(0, len(ids), 150):
            try:
                r = requests.get(url.rstrip('/') + '/rest/v1/picks', timeout=30, headers=hdr,
                                 params={'select': 'id,estado,marcador,resultado_c1',
                                         'id': 'in.(%s)' % ','.join(ids[i:i + 150]), 'estado': 'in.(verde,roja,nula)'})
                if r.status_code == 200:
                    base.update({x['id']: x for x in r.json()})
            except Exception as e:
                logger.warning('[web] no se pudo leer lo ya liquidado: %s', e)
    n = 0
    for p in abiertos:
        b = base.get(p['id'])
        if b and b.get('estado') in FINALES:
            p['estado'] = b['estado']
            for k in ('marcador', 'resultado_c1'):
                if b.get(k) and not p.get(k):
                    p[k] = b[k]
            n += 1
    return n


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    r = construir()
    # v463 — los pendientes que ya terminaron se cierran con su resultado final (ESPN y,
    # si no, Flashscore) ANTES de escribir y subir: si no, se quedaban pendientes para siempre
    try:
        import liquidar_pendientes
        print('web: %d pendientes cerrados con su resultado final' % liquidar_pendientes.cerrar(r['picks']))
    except Exception as e:
        logger.warning('[web] no se cerraron los pendientes: %s', e)
    print('web: %d liquidados que esta pasada iba a devolver a «por jugar»' % no_retroceder(r['picks']))
    secretos = premium(r['picks'])
    analisis = r.pop('analisis', [])
    # v482 — los jugadores y las líneas (VIP) salen de lo público ANTES de escribir y subir;
    # la IA los lee del fichero privado (por id) y la página del VIP, de `picks_vip`
    privado_vip = {f['id']: {'jug': f.get('jug'), 'lin': (f.get('ctx') or {}).get('lin')}
                   for f in r['picks'] + analisis
                   if f.get('id') and (f.get('jug') or (f.get('ctx') or {}).get('lin'))}
    vip = separar_vip(r['picks'] + analisis)
    try:
        os.makedirs(os.path.dirname(PRIVADO_VIP), exist_ok=True)
        with open(PRIVADO_VIP, 'w', encoding='utf-8') as f:
            json.dump(privado_vip, f, ensure_ascii=False)
    except Exception as e:
        logger.warning('[web] sin fichero privado del VIP: %s', e)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    tmp = SALIDA + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(r, f, ensure_ascii=False, indent=0)
    os.replace(tmp, SALIDA)
    # v418 — las tarjetas de «sólo análisis», aparte (la página y la IA las leen)
    try:
        with open(ANALISIS + '.tmp', 'w', encoding='utf-8') as f:
            json.dump({'generado': r.get('generado'), 'analisis': analisis}, f, ensure_ascii=False, indent=0)
        os.replace(ANALISIS + '.tmp', ANALISIS)
        print('web: %d tarjetas de sólo análisis' % len(analisis))
    except Exception as e:
        logger.warning('[web] no se escribió %s: %s', ANALISIS, e)
    # v384 — deportes con partidos hoy pero sin ningún pick (para decirlo en la página)
    try:
        import precalculo_dia as pc
        prons = ((pc.leer() or {}).get('datos') or {}).get('pronosticos') or []
        hoy = dt.datetime.now(dt.timezone(dt.timedelta(hours=-6))).date().isoformat()
        con = {p.get('deporte') for p in r['picks'] if str(p.get('fecha') or '') == hoy}
        sin = {}
        for p in prons:
            dep = str(p.get('deporte') or '')
            if dep and dep not in con and str(p.get('fecha') or p.get('fecha_cdmx') or '')[:10] == hoy:
                sin[dep] = sin.get(dep, 0) + 1
        with open(os.path.join(os.path.dirname(SALIDA), 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({'sin_pick': sin}, f, ensure_ascii=False)
    except Exception as e:
        logger.warning('[web] sin meta: %s', e)
    try:
        os.makedirs(os.path.dirname(PRIVADO), exist_ok=True)
        with open(PRIVADO, 'w', encoding='utf-8') as f:
            json.dump({x['id']: x['apuesta'] for x in secretos}, f, ensure_ascii=False)
    except Exception as e:
        logger.warning('[web] sin fichero privado: %s', e)
    n = subir_supabase(r['picks'], secretos)
    nv = subir_vip(vip)
    print('web: %d partidos con jugadores o líneas en picks_vip (sólo VIP)' % nv)
    # v396 — las combinadas del día (de cada deporte y mixtas): `combinadas_web`.
    # Con el texto real de las patas premium SÓLO para compararlo con la IA; a la
    # tabla pública va el texto tapado.
    nc = 0
    try:
        import combinadas_web
        url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
        if url and key:
            reales = {x['id']: x['apuesta'] for x in secretos}
            nc = combinadas_web.subir([dict(p, _real=reales.get(p['id'])) for p in r['picks']], url, key)
    except Exception as e:
        logger.exception('[web] no se pudieron sincronizar las combinadas')
        raise RuntimeError('No se pudo sincronizar combinadas; se bloquea la publicación') from e
    # v428 — las combinadas que arman los usuarios: se liquidan con lo ya
    # calificado y, si aciertan, la base les da sus monedillas (nunca la página)
    try:
        import requests
        url, key = os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY')
        if url and key:
            rr = requests.post(url.rstrip('/') + '/rest/v1/rpc/liquidar_combinadas_usuario', timeout=60,
                               headers={'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, json={})
            print('web: combinadas de usuarios liquidadas: %s' % (rr.text[:40] if rr.ok else 'HTTP %s' % rr.status_code))
    except Exception as e:
        logger.warning('[web] no se liquidaron las combinadas de usuarios: %s', e)
    print('web: %d picks en %s; %d subidos a Supabase; %d premium; %d combinadas'
          % (len(r['picks']), SALIDA, n, len(secretos), nc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
