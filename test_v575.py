"""v575 — lo que se manda por Telegram se queda y cuenta: sin avisos de «Cambio»; sólo se avisa si el partido no se completó."""
import datetime as dt
import io
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
import exportar_web as xw
import telegram_canales as tc

AHORA = dt.datetime(2026, 11, 6, 2, tzinfo=dt.timezone.utc)


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_ya_no_hay_aviso_de_cambio():
    t = leer('telegram_canales.py')
    assert 'ya no lo contamos' not in t and 'ya no recomendamos' not in t and '_avisos_retiro' not in t and '_retirados' not in t
    assert tc.VENTANA_GRATIS_H == 4 and tc.VENTANA_APUESTA_H == 4        # gratis y VIP, cerca del partido


def _nula(**k):
    return dict({'id': 'p1', 'estado': 'nula', 'apuesta': 'Pick', 'partido': 'A vs B', 'inicio': '2026-11-05 20:00:00'}, **k)


def test_se_avisa_solo_si_el_partido_no_se_completo():
    tc._DETALLES.clear()
    tc._DETALLES[('p1', 'vip')] = {'pick': 'p1', 'canal': 'vip', 'texto': 'Gana A', 'partido': 'A vs B', 'inicio': '2026-11-05 20:00:00'}
    try:
        m = tc._avisos_anulados([_nula(), _nula(id='p2'), _nula(id='p3', estado='roja')], set(), 'vip', AHORA)
        assert len(m) == 1 and 'Pick anulado' in m[0][0] and 'Gana A' in m[0][0] and m[0][1] == [('p1', 'vip', 'anulado')]   # p2 no se enseñó; p3 perdió
        assert tc._avisos_anulados([_nula()], {('p1', 'vip', 'anulado')}, 'vip', AHORA) == []                                  # una vez
        assert tc._avisos_anulados([_nula()], set(), 'gratis', AHORA) == []                                                     # sólo a donde se mandó
        assert tc._avisos_anulados([_nula(inicio='2026-11-01 20:00:00')], set(), 'vip', AHORA) == []                           # nada viejo de golpe
    finally:
        tc._DETALLES.clear()


class R:
    def __init__(self, d, ok=True):
        self._d, self.ok = d, ok

    def json(self):
        return self._d


def _con_base(fn, enviados, filas, premium=()):
    import requests
    antes = requests.get
    env = {k: os.environ.get(k) for k in ('SUPABASE_URL', 'SUPABASE_SERVICE_KEY')}
    os.environ.update(SUPABASE_URL='https://x', SUPABASE_SERVICE_KEY='k')

    def falso(url, **k):
        if 'telegram_enviados' in url:
            assert k['params']['texto'] == 'not.is.null' and k['params']['tipo'] == 'eq.pick'
            return R(enviados)
        if url.endswith('picks_premium'):
            return R(list(premium))
        return R([f for f in filas if f['id'] in k['params']['id']])
    requests.get = falso
    try:
        return fn()
    finally:
        requests.get = antes
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_lo_mandado_vuelve_a_la_lista():
    picks = [{'id': 'a', 'apuesta': 'Gana A', 'estado': 'pendiente', 'cuota': 1.2}]
    filas = [{'id': 'b', 'apuesta': '🔒 Pick Platino', 'estado': 'pendiente', 'cuota': 1.3, 'creado': 'x'}, {'id': 'c', 'apuesta': 'Gana C', 'estado': 'roja', 'cuota': 1.4},
             {'id': 'd', 'apuesta': 'Gana D', 'estado': 'verde', 'cuota': 1.5}]
    env = [{'pick': 'a'}, {'pick': 'b'}, {'pick': 'comb:c+d'}, {'pick': 'noexiste'}]
    n = _con_base(lambda: xw.retener_enviados(picks), env, filas, [{'id': 'b', 'apuesta': 'Goles: Más de 2.5'}])
    assert n == 3 and [p['id'] for p in picks] == ['a', 'b', 'c', 'd']
    assert picks[1]['apuesta'] == 'Goles: Más de 2.5'                    # el texto real; luego `premium` lo tapa si toca
    assert picks[2]['estado'] == 'roja'                                   # el rojo cuenta
    assert set(picks[1]) == set(picks[0])                                 # las mismas columnas: Supabase rechaza lotes disparejos


def test_si_algo_falla_no_rompe_la_pasada():
    picks = [{'id': 'a'}]
    assert _con_base(lambda: xw.retener_enviados(picks), [], []) == 0 and picks == [{'id': 'a'}]
    import requests
    antes = requests.get
    os.environ.update(SUPABASE_URL='https://x', SUPABASE_SERVICE_KEY='k')

    def error(*a, **k):
        raise ValueError('sin red')
    requests.get = error
    try:
        assert xw.retener_enviados(picks) == 0 and len(picks) == 1
    finally:
        requests.get = antes
        os.environ.pop('SUPABASE_URL', None)
        os.environ.pop('SUPABASE_SERVICE_KEY', None)


def test_el_orden_en_el_exportador():
    s = leer('exportar_web.py')
    assert s.index("retener_enviados(r['picks'])") < s.index("liquidar_pendientes.cerrar(r['picks'])") < s.index("premium(r['picks'])")


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
