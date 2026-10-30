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
