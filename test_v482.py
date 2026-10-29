#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v482 — bug 4: los jugadores y las líneas (VIP) salen de lo público (hoy.json, analisis.json, tabla
`picks`) y van a `picks_vip`, que sólo lee el VIP. La IA los toma del fichero privado. Sin red."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    import exportar_web as ew
    lin = {'casa': True, 'corners': {'h': [['mas', 4.5, 0.8, 1.3]]}, 'par': [['corners', 'h', 4.5, 0.8, 1.3]]}
    ctx = {'fl': 'GGE', 'lin': lin}                       # compartido entre los picks del partido
    filas = [{'id': 'a1', 'fecha': '2026-10-28', 'partido': 'A vs B', 'ctx': ctx, 'jug': {'h': [{'n': 'X', 'gol': 0.4}]}},
             {'id': 'a2', 'fecha': '2026-10-28', 'partido': 'A vs B', 'ctx': ctx},
             {'id': 'c1', 'fecha': '2026-10-28', 'partido': 'C vs D', 'ctx': {'fl': 'EEE'}}]
    vip = ew.separar_vip(filas)
    check(all(f.get('jug') is None and 'lin' not in (f.get('ctx') or {}) for f in filas),
          'v482: ninguna fila pública lleva jugadores ni líneas')
    check(filas[0]['ctx']['fl'] == 'GGE' and ctx.get('lin') is lin, 'v482: lo gratis del contexto se queda y el ctx compartido no se toca')
    check([f['vip_hay'] for f in filas] == [True, True, False], 'v482: `vip_hay` marca el 🔒 de quien no es VIP')
    v = vip.get('2026-10-28|A vs B') or {}
    check(len(vip) == 1 and v.get('lin') is lin and v.get('jug', {}).get('h') and v.get('clave') == '2026-10-28|A vs B',
          'v482: un registro por partido con sus jugadores y líneas para picks_vip')
    src = open('exportar_web.py', encoding='utf-8').read()
    m = src.split('def main()')[1]
    check(m.index('separar_vip(') < m.index('json.dump(r, f') < m.index('subir_supabase(r['),
          'v482: se separa ANTES de escribir hoy.json y de subir a la tabla pública')
    check('/rest/v1/picks_vip' in src.split('def _lin_publicadas')[1].split('def ')[0],
          'v482: las líneas con casa de la pasada anterior se leen de picks_vip, no de lo público')
    ia = open('ia_gemini.py', encoding='utf-8').read()
    check("'vip.json'" in ia and "p['jug'] = v['jug']" in ia, 'v482: la IA toma los jugadores del fichero privado')
    cu = open(os.path.join('web', 'cuenta.js'), encoding='utf-8').read()
    ap = open(os.path.join('web', 'app.js'), encoding='utf-8').read()
    check("sb.from('picks_vip')" in cu and 'yo.vip[x.fecha' in cu, 'v482: la página del VIP pide picks_vip con su sesión')
    check('conVip(ps).ctx' in ap and '!!vipHay' in ap, 'v482: la tarjeta usa lo del VIP y el 🔒 con vip_hay')
    sql = open(os.path.join('supabase', 'v482_picks_vip.sql'), encoding='utf-8').read()
    check('using (public.es_pro())' in sql and 'revoke all on public.picks_vip from anon' in sql,
          'v482: la base sólo deja leer picks_vip al VIP')
    probar_kbo()


def probar_kbo():
    import tempfile
    import pandas as pd
    import kbo_naver as kn
    filas = []
    for a in (2024, 2025, 2026):
        for i in range(40):
            filas.append({'date': '%d-05-%02d' % (a, 1 + i % 28), 'home_team': 'L%d' % (i % 7), 'away_team': 'V%d' % i,
                          'game_id': 'g%d%d' % (a, i), 'estadio': 'x', 'home_runs': 5 if i % 9 < 5 else 1,
                          'away_runs': 3, 'home_pitcher': '', 'away_pitcher': ''})
    ruta = os.path.join(tempfile.mkdtemp(), 'historico_kbo.csv')
    pd.DataFrame(filas).to_csv(ruta, index=False)
    pedidas = []
    nuevo = pd.DataFrame([dict(filas[-1], date=pd.Timestamp(filas[-1]['date']), home_runs=9),
                          dict(filas[-1], date=pd.Timestamp('2026-10-25'), game_id='nuevo')])
    viejo = kn.descargar_temporada
    kn.descargar_temporada = lambda a, solo_finalizados=True: (pedidas.append(a), nuevo if a == 2026 else pd.DataFrame())[1]
    try:
        df = kn.actualizar(list(range(2024, 2027)), salida=ruta)
    finally:
        kn.descargar_temporada = viejo
    check(pedidas == [2026], 'v482 KBO: sólo se baja la temporada del último juego guardado (no 2008-hoy)')
    check(len(df) == 121 and (df['date'].dt.year == 2024).sum() == 40 and (df['home_runs'] == 9).sum() == 1,
          'v482 KBO: lo guardado se queda y lo nuevo se suma (121 juegos)')
    src = open('kbo_naver.py', encoding='utf-8').read()
    check('pd.Timestamp(ini) > pd.Timestamp.today()' in src, 'v482 KBO: no se piden los meses que no han llegado')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
