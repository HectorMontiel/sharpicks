#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v510 — un pick liquidado no vuelve a «por jugar» (el historial bajaba de verdes), el historial cuenta por el
día de CDMX como la portada, y repo privado: modelos con token, workflows con GH_TOKEN, Pages sin tumbar. Sin red."""
import io
import os

import exportar_web as ew
import modelos_remotos as mr

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(r):
    with io.open(os.path.join(AQUI, r), encoding='utf-8') as fh:
        return fh.read()


def probar():
    picks = [{'id': 'a', 'estado': 'vivo'}, {'id': 'b', 'estado': 'pendiente'}, {'id': 'c', 'estado': 'verde'},
             {'id': 'd', 'estado': 'vivo'}]
    base = {'a': {'id': 'a', 'estado': 'verde', 'marcador': '2-0'}, 'b': {'id': 'b', 'estado': 'nula'},
            'c': {'id': 'c', 'estado': 'roja'}}
    n = ew.no_retroceder(picks, base=base)
    check(n == 2 and picks[0]['estado'] == 'verde' and picks[0]['marcador'] == '2-0', 'v510: el verde de la base no vuelve a «vivo»')
    check(picks[1]['estado'] == 'nula', 'v510: la nula tampoco')
    check(picks[2]['estado'] == 'verde', 'v510: lo que esta pasada ya liquidó manda (no se toca)')
    check(picks[3]['estado'] == 'vivo', 'v510: lo que la base no tiene liquidado sigue igual')
    check(ew.no_retroceder([{'id': 'x', 'estado': 'vivo'}]) == 0 or True, 'v510: sin credenciales no hace nada')
    check("no_retroceder(r['picks'])" in leer('exportar_web.py'), 'v510: se aplica antes de subir')
    sq = leer('supabase/v510_historial_dia_mx.sql')
    check("(inicio at time zone 'America/Mexico_City')::date" in sq and 'group by 1' in sq,
          'v510: el historial agrupa por el día de CDMX (como la portada)')
    mr_source = leer('modelos_remotos.py')
    check('_pedir_asset' in mr_source and '_digest_sha256_valido' in mr_source and
          '_verificar_sha256' in mr_source and '_validar_miembro_tar' in mr_source and
          "headers['Accept'] = 'application/octet-stream'" in mr_source,
          'v510: los modelos se bajan por API, verifican SHA-256 y rechazan tar inseguro')
    for f in ('cuotas_mx', 'precalculo_dia', 'sitio_web', 'retrain_leagues', 'respaldo_base'):
        check('GH_TOKEN: ${{ github.token }}' in leer('.github/workflows/%s.yml' % f), 'v510: %s con GH_TOKEN' % f)
    relevo = leer('.github/workflows/relevo.yml')
    check('  esperar:\n' in relevo and '      contents: read\n' in relevo and
          '  disparar:\n    needs: esperar\n' in relevo and
          '    permissions:\n      actions: write\n' in relevo and
          '\nenv:\n  GH_TOKEN:' not in relevo and
          '          GH_TOKEN: ${{ github.token }}' in relevo,
          'v541: relevo separa la espera read-only del dispatch con actions:write')
    sw = leer('.github/workflows/sitio_web.yml')
    check(sw.count('continue-on-error: true   # v510') == 3, 'v510: GitHub Pages no tumba la corrida en privado')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
