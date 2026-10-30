"""v548 — los tickets con apuesta de 5,000 a 19,999 y el aviso censurado del VIP en el canal gratis."""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_monto_entre_5000_y_20000():
    import tarjeta_tg as t
    vistos = {t.monto([{'partido': 'A%d vs B' % i, 'apuesta': 'Gana A%d' % i}]) for i in range(60)}
    assert vistos <= set(range(5000, 20000)) and 10000 in vistos and len(vistos) > 2
    p = [{'partido': 'X vs Y', 'apuesta': 'Gana X'}]
    assert t.monto(p) == t.monto(p)                                   # el mismo ticket, la misma cifra
    assert t._pesos(10600) == '$10,600'


def test_gratis_recibe_el_vip_censurado():
    import telegram_canales as tc
    os.environ.pop('TELEGRAM_VIP_NIVELES', None)
    ahora = dt.datetime(2026, 10, 30, 18, 0, tzinfo=dt.timezone.utc)          # 12:00 CDMX
    ini = (ahora + dt.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    ps = [{'id': 'v1', 'partido': 'Popko D. vs MacKinlay J.', 'deporte': 'Tenis', 'apuesta': 'Gana Popko SECRETO',
           'cuota': 1.06, 'prob': 0.87, 'elige': True, 'estado': 'pendiente', 'inicio': ini}]
    g = tc.armar_gratis(ps, set(), ahora)
    tz = [x for x in g if x[0] and 'Acaban de llegar' in x[0]]
    assert len(tz) == 1
    texto, cubre, img = tz[0]
    assert 'SECRETO' not in texto and '1.06' not in texto and 'Popko D. vs MacKinlay J.' in texto and 'hazte VIP' in texto
    assert img and img[:4] == b'\x89PNG'
    ya = {(c[0], c[1], c[2]) for c in cubre}
    assert not [x for x in tc.armar_gratis(ps, ya, ahora) if x[0] and 'Acaban de llegar' in x[0]]   # no se repite


def test_v549_errores_con_imagen_ia_primero_y_rojas():
    import telegram_canales as tc
    os.environ.pop('TELEGRAM_VIP_NIVELES', None)
    ahora = dt.datetime(2026, 10, 30, 18, 0, tzinfo=dt.timezone.utc)
    ini = (ahora + dt.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    err = {'id': 'e1', 'partido': 'Hlucin vs Sumperk', 'deporte': 'Fútbol', 'apuesta': 'Gana Hlucin', 'cuota': 1.70, 'prob': 0.65,
           'tipo': 'error', 'ventaja': 0.11, 'estado': 'pendiente', 'inicio': ini}
    a = {'id': 'a', 'partido': 'A vs B', 'deporte': 'Tenis', 'apuesta': 'Gana A', 'cuota': 1.1, 'prob': 0.90, 'estado': 'pendiente', 'inicio': ini}
    b = {'id': 'b', 'partido': 'C vs D', 'deporte': 'Tenis', 'apuesta': 'Gana C', 'cuota': 1.2, 'prob': 0.82, 'estado': 'pendiente', 'inicio': ini, '_ia': 5}
    v = tc.armar_vip([err, a, b], set(), ahora)
    e = [x for x in v if 'Error de cuota' in x[0]]
    assert e and len(e[-1]) == 3 and e[-1][2][:4] == b'\x89PNG'                 # el error de cuota lleva su ticket
    h = [x for x in v if 'Ya es hora de apostar' in x[0]][0][0]
    assert h.index('Gana C') < h.index('Gana A') and '✨ Modelo + IA: mayor probabilidad' in h   # la IA primero, con su sello
    assert '✨' not in tc._apuesta(b)                                            # fuera del VIP no se pone
    r1 = dict(a, estado='verde', marcador='2-0'); r2 = dict(b, estado='roja', marcador='0-2')
    res = [x for x in tc.armar_vip([r1, r2], set(), ahora) if 'Resultados VIP' in x[0]][0][0]
    assert '✅ Gana A' in res and '❌ Gana C' in res                              # las rojas también, con nombre
