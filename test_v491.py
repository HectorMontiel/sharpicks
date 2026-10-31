#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v491 — las patas de una combinada fija (empezada o comprada) no se borran aunque el modelo las retire:
antes la pata quedaba «🔒 Pick Platino» para todos (también el VIP), sin abrirse y sin liquidarse. Y si
una pata falta en la lista, abre la ficha de su partido. Sin red."""
import datetime as dt
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


class R:
    def __init__(self, datos, ok=True):
        self.ok, self._d, self.status_code = ok, datos, 200 if ok else 500

    def json(self):
        return self._d


def probar():
    import requests
    import exportar_web as ew
    ahora = dt.datetime.now(dt.timezone.utc)
    antes = (ahora - dt.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    luego = (ahora + dt.timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
    combs = [{'id': 'A', 'patas': [{'id': 'a1', 'inicio': antes}, {'id': 'a2', 'inicio': luego}]},   # empezada
             {'id': 'B', 'patas': [{'id': 'b1', 'inicio': luego}]},                                   # ni empezada ni comprada
             {'id': 'C', 'patas': [{'id': 'c1', 'inicio': luego}]}]                                   # comprada
    viejo = requests.get
    try:
        # v550 — también lo que usan los usuarios: sus combinadas, lo seguido, lo desbloqueado y lo mandado por Telegram
        def falso(u, **k):
            for fin, d in (('/combinadas', combs), ('/desbloqueos_combinada', [{'combinada': 'C'}]), ('/combinadas_usuario', [{'patas': ['u1']}]),
                           ('/seguidos', [{'pick': 's1'}]), ('/desbloqueos', [{'pick': 'd1'}]), ('/telegram_enviados', [{'pick': 't1'}])):
                if u.endswith(fin):
                    return R(d)
            return R([], ok=False)
        requests.get = falso
        fijas = ew._patas_fijas('https://x.supabase.co', 'k')
        requests.get = lambda u, **k: R([], ok=False)
        sin = ew._patas_fijas('https://x.supabase.co', 'k')
    finally:
        requests.get = viejo
    check(fijas == {'a1', 'a2', 'c1', 'u1', 's1', 'd1', 't1'},
          'v491/v550: se conservan las patas de las combinadas empezadas o compradas y lo que usan los usuarios (%s)' % sorted(fijas or []))
    check(sin is None, 'v491: si no se pueden leer las combinadas, no se borra nada en esa pasada')
    src = open(os.path.join(AQUI, 'exportar_web.py'), encoding='utf-8').read()
    check("fijas = _patas_fijas(url, key)" in src and "fijas is not None and not _pasada_incompleta" in src
          and "vivos = ','.join(sorted({p['id'] for p in picks} | fijas))" in src,
          'v491: el borrado de lo retirado respeta las patas fijas')
    app = open(os.path.join(AQUI, 'web', 'app.js'), encoding='utf-8').read()
    check("const alt = kp ? estado.picks.concat(estado.analisis || []).find((q) => clavePartido(q) === kp) : null" in app
          and "(m.get(x.id) || ir ? '<i class=\"comb-ir\">›</i>' : '')" in app,
          'v491: una pata que no está en la lista abre la ficha de su partido')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
