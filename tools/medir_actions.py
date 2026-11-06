#!/usr/bin/env python3
"""Mide lo que Actions consume de verdad: minutos por TRABAJO (lo que se factura en un repo privado) y cuántos
trabajos corren a la vez (lo que dimensiona un runner propio). La duración de la corrida no sirve: incluye colas y
no suma los trabajos en paralelo.

    python tools/medir_actions.py --dias 7 [--json salida.json]

Sólo lee (API de GitHub vía `gh`); no imprime secretos ni contenido de logs.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

REPO = 'HectorMontiel/sharpicks'
PRECIO_MIN = 0.006      # USD, Linux 2 núcleos (docs de facturación de GitHub, consultado 2026-11)
INCLUIDO_USD = 12.0     # lo incluido en el plan Free por mes
UTC = dt.timezone.utc


def _gh(*args: str) -> str:
    return subprocess.run(('gh', 'api', *args), capture_output=True, text=True, encoding='utf-8', check=True).stdout


def _t(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def corridas(dias: int) -> list:
    desde = (dt.datetime.now(UTC) - dt.timedelta(days=dias)).strftime('%Y-%m-%d')
    out = _gh('--paginate', '-X', 'GET', f'repos/{REPO}/actions/runs', '-f', 'per_page=100', '-f', 'created=>=' + desde,
              '--jq', '.workflow_runs[]|[.id,.name]|@json')
    return [json.loads(x) for x in out.splitlines()]


def trabajos(corrida: list) -> list:
    rid, nombre = corrida
    try:
        out = _gh('--paginate', f'repos/{REPO}/actions/runs/{rid}/jobs?per_page=100',
                  '--jq', '.jobs[]|[.name,.started_at,.completed_at,.conclusion]|@json')
    except subprocess.CalledProcessError:
        return []
    filas = []
    for x in out.splitlines():
        job, ini, fin, con = json.loads(x)
        a, b = _t(ini), _t(fin)
        if a and b and b >= a and con != 'skipped':
            filas.append({'flujo': nombre, 'job': job, 'ini': a, 'fin': b, 'min': (b - a).total_seconds() / 60})
    return filas


def resumen(filas: list, dias: int, excluir: tuple = ()) -> dict:
    por = collections.defaultdict(lambda: [0, 0.0])
    for f in filas:
        por[f['flujo']][0] += 1
        por[f['flujo']][1] += f['min']
    total = sum(v[1] for v in por.values())
    eventos = sorted([(f['ini'], 1) for f in filas if f['flujo'] not in excluir] +
                     [(f['fin'], -1) for f in filas if f['flujo'] not in excluir], key=lambda e: (e[0], e[1]))
    ahora, pico, seg, ult = 0, 0, collections.Counter(), None
    for t, d in eventos:
        if ult is not None:
            seg[ahora] += (t - ult).total_seconds()
        ahora += d
        pico = max(pico, ahora)
        ult = t
    tot_seg = sum(seg.values()) or 1
    mes = total / dias * 30
    return {'dias': dias, 'por_flujo': {k: {'trabajos': v[0], 'min': round(v[1])} for k, v in sorted(por.items(), key=lambda x: -x[1][1])},
            'min_total': round(total), 'min_mes': round(mes), 'usd_mes_alojado': round(max(0, mes * PRECIO_MIN - INCLUIDO_USD), 2),
            'pico_simultaneos': pico, 'tiempo_con_n': {str(k): round(100 * v / tot_seg, 1) for k, v in sorted(seg.items())}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dias', type=int, default=7)
    ap.add_argument('--json')
    a = ap.parse_args()
    cs = corridas(a.dias)
    with ThreadPoolExecutor(8) as ex:
        filas = [f for fs in ex.map(trabajos, cs) for f in fs]
    r = resumen(filas, a.dias, excluir=('Relevo de las dos horas',))
    sin = resumen([f for f in filas if f['flujo'] != 'Relevo de las dos horas'], a.dias)
    r['sin_relevo'] = {k: sin[k] for k in ('min_total', 'min_mes', 'usd_mes_alojado')}
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
