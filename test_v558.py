"""v558 — el método del usuario (cumplimiento en sus últimos 10 y 5) en el botón «Armar parley» de cualquier partido."""
import io
import json
import os

import pandas as pd

import parley_metodo as pm

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def historia(n=12):
    """A y B juegan contra otros: A siempre hace 6 córners y recibe 4; B hace 3 y recibe 5."""
    filas = []
    for i in range(n):
        d = pd.Timestamp('2026-09-01') + pd.Timedelta(days=i)
        filas.append({'date': d, 'home_team': 'A', 'away_team': 'X%d' % i, 'home_corners': 6, 'away_corners': 4, 'home_goals': 2, 'away_goals': 1,
                      'home_yellow': 2, 'away_yellow': 1, 'home_red': 0, 'away_red': 0})
        filas.append({'date': d, 'home_team': 'Y%d' % i, 'away_team': 'B', 'home_corners': 5, 'away_corners': 3, 'home_goals': 0, 'away_goals': 0,
                      'home_yellow': 1, 'away_yellow': 3, 'home_red': 0, 'away_red': 0})
    return pd.DataFrame(filas)


ANTES = pd.Timestamp('2026-11-05')


def test_escalera_quita_las_lineas_de_otro_mercado():
    # el caso real: «más de 1,5» a 2,12 bajo corners
    tabla = {'1.5': {'p': .43, 'mas': 2.12, 'menos': 1.7}, '7.5': {'p': .79, 'mas': 1.2, 'menos': 3.6}, '9.5': {'p': .52, 'mas': 1.75, 'menos': 1.95}}
    assert [x[0] for x in pm.escalera_limpia('corners', tabla)] == [9.5, 7.5]
    # aunque la línea mínima no la hubiera quitado, la probabilidad que baja al bajar la línea sí
    tabla = {'6.5': {'p': .40, 'mas': 2.2, 'menos': 1.6}, '9.5': {'p': .52, 'mas': 1.75, 'menos': 1.95}}
    assert [x[0] for x in pm.escalera_limpia('corners', tabla)] == [9.5]


def test_fotos_viejas_no_rompen():
    assert pm.escalera_limpia('goles', {'2.5': .5}) == []
    assert pm.escalera_limpia('goles', None) == []


def test_cuenta_al_equipo_y_al_rival():
    m = {'corners_home': {'4.5': {'p': .6, 'mas': 1.6, 'menos': 2.2}}}
    x = pm.pozo(historia(), 'A', 'B', ANTES, m)[0]
    # A hace 6 (> 4,5) y B concede 5 (> 4,5): cumplieron todos en las dos ventanas
    assert x[:6] == ['corners', 'h', 'mas', 4.5, 1.6, .6]
    assert x[7:11] == [20, 20, 10, 10]
    assert x[6] == round(31 / 32, 3)
    assert x[11:] == [5, 6]


def test_totales_con_los_partidos_de_cada_uno():
    m = {'corners': {'8.5': {'p': .55, 'mas': 1.7, 'menos': 2.0}}}
    r = pm.pozo(historia(), 'A', 'B', ANTES, m)
    x = [y for y in r if y[2] == 'mas'][0]
    # los partidos de A suman 10 (> 8,5) y los de B suman 8 (no): cumplió la mitad
    assert x[1] == 't' and x[7:] == [10, 20, 5, 10, 8, 10]


def test_sin_fuga_ni_poca_historia():
    h = historia()
    corte = pd.Timestamp('2026-09-04')          # sólo 3 partidos antes de esa fecha
    m = {'corners_home': {'4.5': {'p': .6, 'mas': 1.6, 'menos': 2.2}}}
    assert pm.pozo(h, 'A', 'B', corte, m) is None
    # un partido del mismo día o posterior no cuenta
    fut = h.iloc[[0]].assign(date=ANTES, home_corners=0)
    otro = pd.concat([h, fut], ignore_index=True)
    assert pm.pozo(otro, 'A', 'B', ANTES, m)[0][7] == 20


def test_cuota_fuera_de_rango_no_entra():
    m = {'corners_home': {'4.5': {'p': .6, 'mas': 2.5, 'menos': 1.05}}}
    assert pm.pozo(historia(), 'A', 'B', ANTES, m) is None
    assert pm.pozo(historia(), 'A', 'B', ANTES, None) is None


def test_ordena_y_limita_por_estadistica():
    m = {'corners_home': {'%d.5' % k: {'p': .9 - k / 20, 'mas': 1.2 + k / 10, 'menos': 1.5} for k in range(2, 8)}}
    r = pm.pozo(historia(), 'A', 'B', ANTES, m)
    assert len(r) == pm.POR_LADO
    assert [x[6] for x in r] == sorted((x[6] for x in r), reverse=True)
    json.dumps(r)                                # va a la base tal cual


def test_los_totales_no_tapan_a_los_equipos():
    # muchas líneas de total con cumplimiento perfecto y una de equipo: la de equipo sigue entre las candidatas
    m = {'corners': {'%d.5' % k: {'p': .95 - k / 40, 'mas': 1.2 + k / 20, 'menos': 2.1} for k in range(5, 8)},
         'corners_home': {'3.5': {'p': .7, 'mas': 1.4, 'menos': 2.2}}, 'corners_away': {'3.5': {'p': .5, 'mas': 1.9, 'menos': 1.8}}}
    r = pm.pozo(historia(), 'A', 'B', ANTES, m)
    assert {x[1] for x in r} == {'t', 'h', 'a'}
    assert sum(x[1] == 't' for x in r) <= pm.POR_LADO


def test_llega_solo_al_vip():
    e = leer('errores_web.py')
    assert "lin['met'] = met" in e and 'parley_metodo.pozo(h, home, away, antes, casa)' in e
    ex = leer('exportar_web.py')
    assert "f['ctx'] = {k: x for k, x in ctx.items() if k != 'lin'}" in ex    # lo público no lleva `lin`


def test_la_pagina():
    a = leer('web', 'app.js')
    assert 'metodoBloque(ps, L, V) +' in a and 'function metPatas(s, q)' in a
    assert 'MET_FACTOR = { 2: 1.01, 3: 1.05, 4: 1.09 }' in a
    assert "p.deporte !== 'Fútbol' || faseDe(ps) !== 'proximo'" in a
    assert 'puede pagar menos' in a and 'no una ganancia asegurada' in a
    assert 'if (lin.met && lin.met.length >= 2) return' in a
    assert '[data-met-k]' in a
    assert "['equipo', 'Por equipo']" in a and "x[1] === 't'" in a and 'data-met-modo' in a
    assert "s.modo === 'equipo' ? x[0] + x[1] : x[0]" in a
    assert '.met-pata {' in leer('web', 'estilo.css')


if __name__ == '__main__':
    # la suite corre cada prueba como script: sin esto, estas funciones no se ejecutan y siempre sale «sin fallos»
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
