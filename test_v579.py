"""v579 — lo que cobró el VIP llega al canal gratis como invitación, no como «¡ganamos!»."""
import io as _io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
import tarjeta_tg
import telegram_canales as tc


def leer(*p):
    return _io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_la_imagen_se_genera():
    from PIL import Image
    pa = [{'partido': 'A vs B', 'apuesta': 'Goles de A: menos de 1.5', 'marcador': '6-1'}]
    for num in ({'v': 470, 'r': 112}, None):
        b = tarjeta_tg.invita_vip('Parley del partido', pa, 12000, 1.34, num, aprox=True)
        assert len(b) > 5000
        assert Image.open(_io.BytesIO(b)).size[0] == tarjeta_tg.ANCHO


def test_el_texto_invita_y_no_dice_ganaste():
    tc._NUMEROS_VIP['d'] = {'v': 470, 'r': 112}
    try:
        t = tc.texto_invita([({'apuesta': 'Gana A', 'partido': 'A vs B'}, {'marcador': '2-0'})], 12000, 1.34, True, aprox=True)
    finally:
        tc._NUMEROS_VIP.clear()
    assert 'Esto no lo vieron aquí' in t and 'Únete al VIP' in t and 'Gana A' in t and '470 ✅ · 112 ❌' in t and 'ganaste' not in t and '~+$4,080' in t


def _armar(vip):
    tc._TICKETS.clear()
    tc._NUMEROS_VIP['d'] = {'v': 80, 'r': 20}
    tc._TICKETS[('ticket:a', 'vip' if vip else 'gratis')] = json.dumps({'titulo': 'Parley', 'vip': vip, 'monto': 10000, 'patas': [{'id': 'p1', 'apuesta': 'Gana A', 'partido': 'A vs B', 'cuota': 1.3}]})
    picks = [{'id': 'p1', 'estado': 'verde', 'marcador': '2-0'}]
    try:
        return tc.armar_ganados(picks, set(), final_de=lambda *a: None)
    finally:
        tc._TICKETS.clear()
        tc._NUMEROS_VIP.clear()


def test_el_vip_y_el_gratis_reciben_cosas_distintas():
    o = _armar(True)
    assert '¡PICK CUMPLIDO!' in o['vip'][0][0] and 'ganaste' in o['vip'][0][0] and 'Esto no lo vieron' not in o['vip'][0][0]
    assert 'Esto no lo vieron aquí' in o['gratis'][0][0] and 'CUMPLIDO' not in o['gratis'][0][0]


def test_lo_propio_del_gratis_sigue_siendo_ganamos():
    o = _armar(False)
    assert o['vip'] == [] and '¡PICK CUMPLIDO!' in o['gratis'][0][0] and 'Esto no lo vieron' not in o['gratis'][0][0]


def test_el_parley_del_partido_tambien():
    t = leer('telegram_canales.py')
    assert "tarjeta_tg.invita_vip('Parley del partido', patas, apuesta, cuota, numeros_vip(), aprox=True) if canal == 'gratis'" in t
    assert 'Esto les llegó a los VIP antes del partido' not in t
    assert "'estado': 'in.(verde,roja)'" in t                       # los números cuentan verdes y rojas


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
