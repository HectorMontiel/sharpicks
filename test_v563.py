"""v563 — Telegram: la foto es un parley que se puede ganar; en el gratis sólo se esconde la jugada; y al cumplirse, foto de «¡ganamos!»."""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarjeta_tg as t
import telegram_canales as tc

AHORA = dt.datetime(2026, 11, 5, 18, 0, tzinfo=dt.timezone.utc)


def pick(i, partido=None, estado='pendiente', cuota=1.2, prob=.85, nivel='Diamante'):
    return {'id': 'p%d' % i, 'partido': partido or 'L%d vs V%d' % (i, i), 'apuesta': 'SECRETO %d' % i, 'cuota': cuota, 'prob': prob, 'estado': estado,
            'nivel': nivel, 'deporte': 'Fútbol', 'inicio': (AHORA + dt.timedelta(hours=2)).isoformat(), 'marcador': '2-1', 'elige': True}


def test_parley_con_partidos_distintos():
    ps = [pick(1), pick(2, 'L1 vs V1'), pick(3), pick(4), pick(5)]        # el 2 es del mismo partido que el 1 (FC Lugano salía dos veces)
    assert [p['id'] for p in tc.parley_de(ps)] == ['p1', 'p3', 'p4']


def test_censurado_ensena_cuota_y_ganancia_pero_no_la_jugada():
    a = t.ticket('x', [{'partido': 'A vs B', 'apuesta': '', 'cuota': 1.5, 'prob': None, 'cuando': 'HOY'}], 'VIP', censurado=True, apuesta=10000)
    b = t.ticket('x', [{'partido': 'A vs B', 'apuesta': '', 'cuota': 2.5, 'prob': None, 'cuando': 'HOY'}], 'VIP', censurado=True, apuesta=10000)
    assert a[:4] == b'\x89PNG' and a != b                                 # la cuota sí se dibuja: cambia la imagen
    # la jugada nunca llega a dibujarse
    x = t.ticket('x', [{'partido': 'A vs B', 'apuesta': 'SECRETO', 'cuota': 1.5, 'prob': None, 'cuando': 'HOY'}], 'VIP', censurado=True, apuesta=10000)
    assert x == a


def test_mismo_monto_en_las_tres_fotos():
    ps = [pick(1), pick(3)]
    assert tc._monto(ps) == tc._monto(ps) == t.monto([{'partido': p['partido'], 'apuesta': p['apuesta']} for p in ps])


def _registra(ps, canal, vip=True):
    x = tc._cubre_ticket(ps, canal, 'Parley VIP', vip)
    tc._TICKETS[(x[0], x[1])] = x[3]
    return x


def test_ganado_a_los_dos_canales_una_vez():
    tc._TICKETS.clear()
    ps = [pick(1), pick(3)]
    k = _registra(ps, 'vip')[0]
    _registra(ps, 'gratis')                                                # el censurado, con las mismas patas
    fin = [dict(p, estado='verde') for p in ps]
    g = tc.armar_ganados(fin, set())
    assert len(g['vip']) == 1 and len(g['gratis']) == 1
    assert g['vip'][0][1] == [(k, 'vip', 'ganado')] and g['vip'][0][2][:4] == b'\x89PNG'
    assert '1.44' in g['vip'][0][0] and 'ganaste' in g['vip'][0][0]
    assert 'VIP antes del partido' in g['gratis'][0][0] and 'VIP antes del partido' not in g['vip'][0][0]
    # no se repite
    assert tc.armar_ganados(fin, {(k, 'vip', 'ganado'), (k, 'gratis', 'ganado')}) == {'vip': [], 'gratis': []}


def test_sin_foto_mientras_falte_o_si_hay_roja():
    tc._TICKETS.clear()
    ps = [pick(1), pick(3)]
    _registra(ps, 'vip')
    for e in (('verde', 'pendiente'), ('verde', 'roja'), ('nula', 'nula')):
        fin = [dict(ps[0], estado=e[0]), dict(ps[1], estado=e[1])]
        assert tc.armar_ganados(fin, set()) == {'vip': [], 'gratis': []}, e
    assert tc.armar_ganados([ps[0]], set()) == {'vip': [], 'gratis': []}    # una pata que ya no está: no se inventa


def test_la_nula_no_cuenta_y_paga_la_cuota_del_envio():
    tc._TICKETS.clear()
    ps = [pick(1, cuota=1.5), pick(3, cuota=2.0)]
    _registra(ps, 'vip')
    # la cuota de hoy cambió: manda la de cuando se mandó
    fin = [dict(ps[0], estado='verde', cuota=9.9), dict(ps[1], estado='nula')]
    txt = tc.armar_ganados(fin, set())['vip'][0][0]
    assert '<b>1.50</b>' in txt and 'PICK CUMPLIDO' in txt and '9.9' not in txt


def test_lo_gratis_se_queda_en_el_gratis():
    tc._TICKETS.clear()
    ps = [pick(1, nivel='Oro')]
    _registra(ps, 'gratis', vip=False)
    g = tc.armar_ganados([dict(ps[0], estado='verde')], set())
    assert not g['vip'] and len(g['gratis']) == 1


def test_el_tope_por_pasada():
    tc._TICKETS.clear()
    fin = []
    for i in range(1, 7):
        p = pick(i)
        _registra([p], 'vip')
        fin.append(dict(p, estado='verde'))
    g = tc.armar_ganados(fin, set())
    assert len(g['vip']) == tc.MAX_GANADOS and len(g['gratis']) == tc.MAX_GANADOS


def test_armar_vip_registra_el_parley():
    tc._TICKETS.clear()
    ps = [pick(1), pick(2, 'L1 vs V1'), pick(3), pick(4), pick(5)]
    lote = [x for x in tc.armar_vip(ps, set(), AHORA) if x[0] and 'hora de apostar' in x[0]][-1]
    filas = [f for f in lote[1] if f[2] == 'ticket']
    assert len(filas) == 1 and filas[0][1] == 'vip'
    d = json.loads(filas[0][3])
    assert [x['id'] for x in d['patas']] == ['p1', 'p3', 'p4'] and d['vip'] is True and d['monto'] == tc._monto(ps[0:1] + ps[2:4])
    assert lote[2][:4] == b'\x89PNG'


def test_la_foto_de_ganado():
    b = t.ganado('Parley VIP', [{'partido': 'A vs B', 'apuesta': 'Gana A', 'marcador': '2-0'}], 10000, 1.79, 'VIP')
    assert b[:4] == b'\x89PNG' and b == t.ganado('Parley VIP', [{'partido': 'A vs B', 'apuesta': 'Gana A', 'marcador': '2-0'}], 10000, 1.79, 'VIP')


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
