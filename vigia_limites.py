"""v542 — EL VIGILANTE DE LÍMITES. El usuario (30-oct-2026): «no creo que necesitemos al lanzar cambiarnos al plan de
paga, a menos que tú me digas y estés monitoreando cuándo ya estemos en riesgo de colapso… si a los 1000 usuarios es el
límite, a los 800 me tienes que estar avisando… quiero que seas capaz de decirme cuándo tenemos que mejorar la
arquitectura y la infraestructura».

Cada día (GitHub, `vigia_limites.yml`) mide el uso contra los límites del plan GRATIS de Supabase:
  · tráfico de salida (egress) del mes: 5 GB. Es el primer límite que se llena. Supabase no da los bytes en sus registros
    (casi todas las respuestas van comprimidas y sin largo), así que se ESTIMA: las peticiones de las últimas 24 h
    (registros de la API) × el tamaño comprimido de cada consulta, medido repitiendo las más frecuentes;
  · base de datos: 500 MB · usuarios activos del mes: 50 000 · invocaciones de funciones del mes: 500 000;
  · correos de alta del día (Brevo gratis): 300.
Avisa por Telegram (a los administradores ligados) y por correo (BREVO_REMITENTE) al 80 % y al 95 % — de lo medido o de
lo que se proyecta al cierre del mes al ritmo de hoy —, una sola vez por métrica, nivel y mes. Los lunes manda un
resumen corto con cuántos usuarios caben todavía.

Variables: SUPABASE_ACCESS_TOKEN (Management API: registros y SQL), SUPABASE_URL, SUPABASE_SERVICE_KEY,
TELEGRAM_BOT_TOKEN, BREVO_API_KEY, BREVO_REMITENTE. `--seco` mide e imprime sin guardar ni avisar.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PROYECTO = 'lyfmyehvfywnjasinbne'
API = 'https://api.supabase.com/v1/projects/%s' % PROYECTO
GB = 1024 ** 3
# límite del plan gratis, qué hacer al acercarse, y si se proyecta al cierre del mes
LIMITES = {
    'egreso_mes':    (5 * GB, 'GB', 'Pasar Supabase a Pro (US$25 al mes, 250 GB) o aligerar lo que baja cada visita.', True),
    'base_mb':       (500, 'MB', 'Pasar Supabase a Pro (8 GB) o borrar historia vieja que ya no se enseña.', False),
    'mau':           (50000, 'usuarios', 'Pasar Supabase a Pro (100 mil usuarios activos al mes).', False),
    'funciones_mes': (500000, 'llamadas', 'Pasar Supabase a Pro (2 millones de llamadas al mes) o espaciar el Pulso.', True),
    'altas_dia':     (300, 'correos', 'Subir de plan en Brevo (los correos de alta se cortan a 300 al día).', False),
}
NIVELES = (95, 80)
NOMBRE = {'egreso_mes': 'Tráfico de salida del mes', 'base_mb': 'Tamaño de la base', 'mau': 'Usuarios activos del mes',
          'funciones_mes': 'Llamadas a funciones del mes', 'altas_dia': 'Correos de alta de hoy'}
UA = {'User-Agent': 'Mozilla/5.0 sharpicks-vigia'}


def _token() -> str:
    t = os.environ.get('SUPABASE_ACCESS_TOKEN')
    if not t:
        sys.exit('vigia: falta SUPABASE_ACCESS_TOKEN')
    return t


def sql(q: str):
    req = urllib.request.Request(API + '/database/query', data=json.dumps({'query': q}).encode(), method='POST',
                                 headers=dict(UA, **{'Authorization': 'Bearer ' + _token(), 'Content-Type': 'application/json'}))
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode() or '[]')


def registros(q: str, ini: dt.datetime, fin: dt.datetime):
    """SQL (ClickHouse) sobre los registros de la API; la ventana no puede pasar de 24 h."""
    u = API + '/analytics/endpoints/logs?' + urllib.parse.urlencode(
        {'sql': q, 'iso_timestamp_start': ini.strftime('%Y-%m-%dT%H:%M:%SZ'), 'iso_timestamp_end': fin.strftime('%Y-%m-%dT%H:%M:%SZ')})
    r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=dict(UA, Authorization='Bearer ' + _token())), timeout=180).read().decode())
    if r.get('error'):
        raise RuntimeError('registros: %s' % r['error'])
    return r.get('result') or []


def tam_comprimido(ruta: str, busca: str) -> int | None:
    """Bytes que de verdad salen (comprimidos) al repetir una consulta GET con la llave de servicio."""
    url, key = os.environ.get('SUPABASE_URL', '').rstrip('/'), os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        return None
    # sin «Mozilla» en el agente: Supabase rechaza la llave secreta nueva (sb_secret_) si la petición parece de navegador
    h = {'User-Agent': 'sharpicks-vigia/1.0', 'apikey': key, 'Accept-Encoding': 'gzip', 'Accept': 'application/json'}
    if key.startswith('eyJ'):                       # la llave vieja (JWT) va también como Bearer; la nueva (sb_secret_) sólo como apikey
        h['Authorization'] = 'Bearer ' + key
    try:
        return len(urllib.request.urlopen(urllib.request.Request(url + ruta + (busca or ''), headers=h), timeout=60).read())   # sin descomprimir: lo del cable
    except Exception as e:
        global _ERR_TAM
        if not _ERR_TAM:
            _ERR_TAM = '%s %s' % (type(e).__name__, getattr(e, 'code', ''))
            print('vigia: no se pudo medir %s (%s)' % (ruta, _ERR_TAM))
        return None


_ERR_TAM = ''


def medir_24h(ahora: dt.datetime, repetir: int = 80) -> dict:
    """Peticiones y tráfico de salida estimado de las últimas 24 h."""
    ini = ahora - dt.timedelta(hours=24)
    filas = registros("select log_attributes['request.method'] m, log_attributes['request.path'] p, log_attributes['request.search'] s, "
                      "count() n from logs where source = 'edge_logs' group by m, p, s order by n desc limit 1000", ini, ahora)
    tot = registros("select log_attributes['request.method'] m, count() n from logs where source = 'edge_logs' group by m", ini, ahora)
    fun = registros("select count() n from logs where source = 'function_edge_logs'", ini, ahora)
    n_get = sum(int(x['n']) for x in tot if x['m'] == 'GET')
    n_otras = sum(int(x['n']) for x in tot if x['m'] not in ('GET', 'OPTIONS'))
    n_opt = sum(int(x['n']) for x in tot if x['m'] == 'OPTIONS')
    gets = [x for x in filas if x['m'] == 'GET' and str(x['p']).startswith('/rest/v1/')]
    medidos, por_ruta = [], {}
    for x in gets[:repetir]:
        b = tam_comprimido(x['p'], x['s'])
        if b is not None:
            medidos.append((int(x['n']), b))
            por_ruta.setdefault(x['p'], []).append(b)
    # lo no medido NO se estima con el promedio ponderado (lo infla la consulta grande de picks): con la mediana
    tams = sorted(b for _, b in medidos)
    prom = tams[len(tams) // 2] if tams else 60000     # sin poder medir nada: un tamaño alto, para no quedarse corto
    cubiertos = sum(n for n, _ in medidos)
    bytes_get = sum(n * b for n, b in medidos)
    resto = max(0, n_get - cubiertos)
    # lo que no se repitió: el promedio de su misma tabla si se midió, si no el promedio general (ponderado)
    otras_get = [x for x in gets[repetir:]]
    for x in otras_get:
        b = por_ruta.get(x['p'])
        bytes_get += int(x['n']) * (sum(b) / len(b) if b else prom)
        resto -= int(x['n'])
    bytes_get += max(0, resto) * 1500                               # auth y lo que no es REST: respuestas chicas
    total = bytes_get + n_otras * 1500 + n_opt * 300 + int(fun[0]['n'] if fun else 0) * 2000
    visitas = sum(int(x['n']) for x in gets if x['p'] == '/rest/v1/ajustes')   # cada carga de la página pide los ajustes una vez
    return {'egreso': int(total), 'peticiones': n_get + n_otras + n_opt, 'funciones': int(fun[0]['n'] if fun else 0),
            'visitas': visitas, 'medidas': len(medidos), 'kb_mediana': round(prom / 1024, 1)}


def foto() -> dict:
    """Lo que se lee directo de la base: tamaño, usuarios activos del mes, total y altas de las últimas 24 h."""
    r = sql("select round(pg_database_size(current_database()) / 1048576.0, 1) base_mb, "
            "(select count(*) from auth.users where last_sign_in_at > now() - interval '30 days') mau, "
            "(select count(*) from auth.users) usuarios, "
            "(select count(*) from auth.users where created_at > now() - interval '24 hours') altas_dia")[0]
    return {k: float(v) for k, v in r.items()}


def pct(v, lim):
    return 100.0 * float(v) / float(lim) if lim else 0.0


def fmt(m, v):
    lim, u, _, _ = LIMITES[m]
    return ('%.2f de %d GB' % (v / GB, lim / GB)) if m == 'egreso_mes' else ('%s de %s %s' % (f'{int(v):,}'.replace(',', ' '), f'{int(lim):,}'.replace(',', ' '), u))


def evaluar(medido: dict, mes_suma: dict, dias_dato: int, hoy: dt.date) -> list:
    """(métrica, nivel, % ahora, % proyectado, texto) de lo que pasa del 80 / 95 %."""
    dias_mes = calendar.monthrange(hoy.year, hoy.month)[1]
    valores = {'egreso_mes': mes_suma.get('egreso', 0), 'funciones_mes': mes_suma.get('funciones', 0),
               'base_mb': medido['base_mb'], 'mau': medido['mau'], 'altas_dia': medido['altas_dia']}
    out = []
    for m, v in valores.items():
        lim, _, accion, proyecta = LIMITES[m]
        ahora_p = pct(v, lim)
        proy = pct(v / max(1, dias_dato) * dias_mes, lim) if proyecta else ahora_p
        nivel = next((n for n in NIVELES if max(ahora_p, proy) >= n), None)
        if nivel:
            t = '%s: %s (%.0f %%).' % (NOMBRE[m], fmt(m, v), ahora_p)
            if proyecta and proy > ahora_p:
                t += ' Al ritmo de este mes cierra en %.0f %%.' % proy
            out.append((m, nivel, ahora_p, proy, t + ' Qué hacer: ' + accion))
    return out


def telegram(texto: str) -> int:
    tok = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not tok:
        return 0
    chats = sql("select distinct t.chat from public.telegram_usuarios t join public.perfiles p on p.id = t.usuario "
                "where coalesce(p.admin, false) and t.chat is not null")
    n = 0
    for c in chats:
        req = urllib.request.Request('https://api.telegram.org/bot%s/sendMessage' % tok, method='POST',
                                     data=json.dumps({'chat_id': c['chat'], 'text': texto, 'parse_mode': 'HTML',
                                                      'disable_web_page_preview': True}).encode(),
                                     headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(req, timeout=30).read()
            n += 1
        except Exception as e:
            print('vigia: Telegram %s: %s' % (c['chat'], type(e).__name__))
    return n


def correo(asunto: str, texto: str) -> bool:
    k, de = os.environ.get('BREVO_API_KEY'), os.environ.get('BREVO_REMITENTE')
    if not k or not de:
        return False
    html = '<div style="font-family:sans-serif;font-size:15px;line-height:1.5">' + texto.replace('\n', '<br>') + '</div>'
    req = urllib.request.Request('https://api.brevo.com/v3/smtp/email', method='POST',
                                 data=json.dumps({'sender': {'name': 'SharPicks', 'email': de}, 'to': [{'email': de}],
                                                  'subject': asunto, 'htmlContent': html}).encode(),
                                 headers={'api-key': k, 'Content-Type': 'application/json', 'accept': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=30).read()
        return True
    except Exception as e:
        print('vigia: correo %s' % type(e).__name__)
        return False


def cupo_usuarios(m24: dict) -> int | None:
    """Cuántos usuarios activos caben en el tráfico del plan gratis, con lo que baja hoy cada visita (1 visita al día)."""
    if not m24.get('visitas'):
        return None
    por_visita = m24['egreso'] / m24['visitas']
    return int(LIMITES['egreso_mes'][0] / (por_visita * 30))


def main(seco: bool = False) -> int:
    ahora = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    hoy = ahora.date()
    m24, f = medir_24h(ahora), foto()
    cupo = cupo_usuarios(m24)
    print('vigia: 24 h → %.1f MB de salida (estimado, %d consultas medidas, %.1f KB la consulta mediana), %d peticiones, %d visitas, %d llamadas a funciones'
          % (m24['egreso'] / 1048576, m24['medidas'], m24['kb_mediana'], m24['peticiones'], m24['visitas'], m24['funciones']))
    print('vigia: base %.1f MB · activos del mes %d · usuarios %d · altas 24 h %d · caben ~%s usuarios activos en el plan gratis'
          % (f['base_mb'], f['mau'], f['usuarios'], f['altas_dia'], cupo if cupo is not None else '?'))
    if seco:
        return 0
    filas = [('egreso', m24['egreso'], LIMITES['egreso_mes'][0], m24), ('funciones', m24['funciones'], LIMITES['funciones_mes'][0], None),
             ('visitas', m24['visitas'], None, None), ('base_mb', f['base_mb'], 500, None), ('mau', f['mau'], 50000, None),
             ('usuarios', f['usuarios'], None, None), ('altas_dia', f['altas_dia'], 300, None)]
    valores = ','.join("('%s', '%s', %s, %s, %s)" % (hoy.isoformat(), m, float(v), 'null' if l is None else float(l),
                                                     "'%s'::jsonb" % json.dumps(d).replace("'", "''") if d else 'null') for m, v, l, d in filas)
    sql('insert into public.vigia_uso (fecha, metrica, valor, limite, detalle) values %s '
        'on conflict (fecha, metrica) do update set valor = excluded.valor, limite = excluded.limite, detalle = excluded.detalle' % valores)
    mes = hoy.strftime('%Y-%m')
    s = sql("select metrica, sum(valor) v, count(*) d from public.vigia_uso where to_char(fecha, 'YYYY-MM') = '%s' "
            "and metrica in ('egreso', 'funciones') group by metrica" % mes)
    mes_suma = {x['metrica']: float(x['v']) for x in s}
    dias_dato = max([int(x['d']) for x in s] or [1])
    ya = {(x['metrica'], int(x['nivel'])) for x in sql("select metrica, nivel from public.vigia_avisos where mes = '%s'" % mes)}
    nuevos = []
    for m, nivel, _, _, texto in evaluar(f, mes_suma, dias_dato, hoy):
        clave_mes = hoy.isoformat() if m == 'altas_dia' else mes
        if (m, nivel) in ya or (clave_mes != mes and sql("select 1 from public.vigia_avisos where mes = '%s' and metrica = '%s' and nivel = %d"
                                                         % (clave_mes, m, nivel))):
            continue
        nuevos.append((clave_mes, m, nivel, texto))
    if nuevos:
        cuerpo = '\n\n'.join(('🔴' if n >= 95 else '🟠') + ' ' + t for _, _, n, t in nuevos)
        msg = '<b>⚠️ SharPicks: hay que actuar pronto</b>\n\n' + cuerpo + '\n\nAvísale a Claude para preparar el cambio.'
        tg, ok = telegram(msg), correo('⚠️ SharPicks: un límite del plan gratis al %d %%' % max(n for _, _, n, _ in nuevos),
                                      msg.replace('<b>', '').replace('</b>', ''))
        print('vigia: %d avisos nuevos → Telegram %d, correo %s' % (len(nuevos), tg, 'sí' if ok else 'no'))
        if tg or ok:
            sql('insert into public.vigia_avisos (mes, metrica, nivel) values %s on conflict do nothing'
                % ','.join("('%s', '%s', %d)" % (c, m, n) for c, m, n, _ in nuevos))
    elif hoy.weekday() == 0 and ahora.hour < 18 and not sql("select 1 from public.vigia_avisos where mes = '%s' and metrica = 'resumen' and nivel = 0"
                                                             % hoy.isoformat()):
        # los lunes, el resumen corto (una vez)
        p = lambda m, v: '%.0f %%' % pct(v, LIMITES[m][0])
        txt = ('<b>📊 SharPicks · semana en verde</b>\n'
               'Tráfico del mes: %s · Base: %s · Activos: %d · Funciones: %s\n'
               '%s') % (p('egreso_mes', mes_suma.get('egreso', 0)), p('base_mb', f['base_mb']), f['mau'],
                        p('funciones_mes', mes_suma.get('funciones', 0)),
                        ('Caben ~%d usuarios activos en el plan gratis.' % cupo) if cupo else '')
        if telegram(txt):
            sql("insert into public.vigia_avisos (mes, metrica, nivel) values ('%s', 'resumen', 0) on conflict do nothing" % hoy.isoformat())
    else:
        print('vigia: todo por debajo del 80 %')
    return 0


if __name__ == '__main__':
    sys.exit(main(seco='--seco' in sys.argv))
