# -*- coding: utf-8 -*-
"""v591 — la IA sólo propone apuesta donde no queda por debajo del modelo: 80 %+ en fútbol y tenis."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_regla_en_la_tarjeta():
    a = leer('web', 'app.js')
    assert "IA_APUESTA_DEPORTES = ['Fútbol', 'Tenis'], IA_APUESTA_MIN = 0.8" in a
    assert 'iaApuestaHtml(a, dep) +' in a
    f = a[a.index('function iaApuestaHtml'):a.index('function iaHtml')]
    assert f.index('IA_APUESTA_DEPORTES.includes(dep)') < f.index('Number(pr) < IA_APUESTA_MIN') < f.index('Lo que metería la IA')
    # no queda otro camino que enseñe la apuesta sin pasar por la regla
    assert a.count('Lo que metería la IA') == 1


def test_la_de_2_horas_manda_y_tambien_pasa_por_la_regla():
    f = leer('web', 'app.js')
    f = f[f.index('function iaApuestaHtml'):f.index('function iaHtml')]
    assert 'dos ? a.mejor_2h : a.mejor_apuesta' in f and 'dos ? a.prob_mejor_2h : a.prob_mejor_apuesta' in f


def test_historial_cuenta_solo_lo_que_propone():
    c = leer('web', 'cuenta.js')
    assert "m.que === 'mejor' && m.banda === '80 % o más' && ['Fútbol', 'Tenis'].includes(m.deporte)" in c
    assert c.count('iaVigente') >= 4
    assert "(x) => x.que === 'mejor' && x.total" not in c
    assert 'no son los mismos partidos' in c


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
