"""v568 — cada deporte con su «Antes del partido» y su plantilla de IA, con lo que de verdad se apuesta en él."""
import datetime as dt
import io
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
import contexto_deportes as cd
import plantillas_deporte as pl


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _p(gf, gc, s=None, c=None, lf=(), lc=(), primero=None, local=True):
    return {'gf': gf, 'gc': gc, 's': s or {}, 'c': c or {}, 'lf': list(lf), 'lc': list(lc), 'primero': primero, 'tid': '1', 'local': local,
            'fecha': dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), 'rival': 'Rival', 'rid': '2', 'nombre': 'Yo', 'nrival': 'Otro', 'id': 'e'}


def test_promedios_nhl_responden_al_mercado():
    ps = [_p(4, 2, {'tir': 30, 'ppg': 1, 'ppo': 4, 'hit': 20}, {'tir': 20}, (1, 2, 1), (0, 1, 1), '1'),
          _p(1, 3, {'tir': 20, 'ppg': 0, 'ppo': 2, 'hit': 10}, {'tir': 30}, (0, 1, 0, 0), (1, 1, 0, 1), '2')]
    x = cd.promedios(ps, 'NHL')
    assert x['n'] == 2 and x['gf'] == 2.5 and x['gc'] == 2.5 and x['tot'] == 5.0
    assert x['o55'] == 0.5 and x['ambos'] == 1.0 and x['p1'] == 1.0                    # 1.er periodo de los dos equipos: 1 y 1
    assert x['pa'] == 0.5 and x['pro'] == 0.5 and x['tir'] == 25 and x['tirc'] == 25   # el 2.º tuvo prórroga (4 periodos)
    assert x['pp'] == round(1 / 6, 2) and x['hit'] == 15


def test_lo_que_no_trae_espn_no_se_inventa():
    x = cd.promedios([_p(100, 90)], 'NBA')
    assert x['gf'] == 100 and 't3' not in x and 'q1' not in x and 'ast' not in x and 'pro' not in x
    assert cd.ultimos([_p(100, 90)], 'NBA')[0][5:] == [None, None, None]


def test_tablas_de_cada_deporte():
    p = _p(110, 100, {'t3': 12, 'reb': 40}, {'t3': 9, 'reb': 44}, (30, 25, 30, 25), (20, 30, 25, 25))
    assert cd.ultimos([p], 'NBA')[0] == ['01/11', 'Rival', 1, 110, 100, [30, 20], [12, 9], [40, 44]]
    q = _p(5, 3, {'hit': 9, 'err': 1}, {'hit': 7, 'err': 0}, (1, 0, 2, 0, 1, 0, 1, 0, 0), (0, 1, 0, 1, 0, 1, 0, 0, 0))
    assert cd.ultimos([q], 'MLB')[0][5:] == [[9, 7], [1, 0], [4, 2]]
    assert cd.promedios([q], 'MLB')['f5'] == 6


def test_forma_mas_reciente_a_la_derecha():
    assert cd._forma([_p(3, 1), _p(1, 3), _p(2, 2)]) == 'EPG'                          # la lista viene del más nuevo al más viejo


def _resumen(comp1='Buffalo Sabres', comp2='Columbus Blue Jackets', fecha='2026-11-07T00:00Z'):
    return {'header': {'competitions': [{'date': fecha, 'competitors': [
        {'homeAway': 'home', 'team': {'id': '1', 'displayName': comp1}}, {'homeAway': 'away', 'team': {'id': '2', 'displayName': comp2}}]}]},
            'injuries': [{'team': {'id': '1'}, 'injuries': [{'athlete': {'displayName': 'Tage T'}, 'status': 'Out'}]}]}


def _calendario(tid, rival):
    evs = []
    for i in range(12):
        evs.append({'id': '%s%d' % (tid, i), 'date': '2026-10-%02dT23:00Z' % (i + 1), 'competitions': [{'status': {'type': {'completed': True}}, 'competitors': [
            {'homeAway': 'home', 'score': {'displayValue': '4'}, 'team': {'id': tid, 'displayName': 'Yo %s' % tid, 'shortDisplayName': 'Yo'}},
            {'homeAway': 'away', 'score': {'displayValue': '2'}, 'team': {'id': rival if i == 0 else '9%d' % i, 'displayName': 'Rival %d' % i, 'shortDisplayName': 'R%d' % i}}]}]})
    # uno futuro y uno sin terminar no cuentan
    evs.append({'id': 'x', 'date': '2026-12-01T23:00Z', 'competitions': [{'status': {'type': {'completed': True}}, 'competitors': []}]})
    evs.append({'id': 'y', 'date': '2026-10-30T23:00Z', 'competitions': [{'status': {'type': {'completed': False}}, 'competitors': []}]})
    return {'events': evs, 'season': {'year': 2027}}


def _con_falso(falso, f):
    antes = cd._get
    cd._get = falso
    cd._MEMO.clear()
    try:
        return f()
    finally:
        cd._get = antes


def _falso(url, params=None):
    if url.endswith('/schedule'):
        if params:
            return {'events': []}
        return _calendario('1', '2') if '/teams/1/' in url else _calendario('2', '1')
    if params and params.get('event') == '999':
        return _resumen()
    return {'boxscore': {'teams': [{'team': {'id': '1'}, 'statistics': [{'name': 'shotsTotal', 'displayValue': '30'}]}]},
            'header': {'competitions': [{'competitors': [{'team': {'id': '1'}, 'linescores': [{'displayValue': '2'}, {'displayValue': '1'}, {'displayValue': '1'}]}]}]}}


def test_contexto_completo():
    p = {'deporte': 'NHL', 'partido': 'Buffalo Sabres vs Columbus Blue Jackets', 'espn': 'hockey/nhl:999'}
    ahora = dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc)
    c = _con_falso(_falso, lambda: cd.contexto(p, ahora))
    assert c['fl'] == 'GGGGG' and c['sl']['n'] == 10 and c['sl']['gf'] == 4 and c['sl']['tir'] == 30
    assert len(c['ul']) == 5 and c['bl'] == ['Tage T (fuera)'] and 'bv' not in c
    assert c['h2h'] == [['01/10/26', 'Yo 1', '4-2', 'Rival 0']]


def test_contexto_sin_datos_o_ya_jugado():
    p = {'deporte': 'NHL', 'partido': 'Buffalo Sabres vs Columbus Blue Jackets', 'espn': 'hockey/nhl:999'}
    tarde = dt.datetime(2026, 11, 9, tzinfo=dt.timezone.utc)
    assert _con_falso(_falso, lambda: cd.contexto(p, tarde)) is None                  # ya se jugó
    assert cd.contexto(dict(p, deporte='Fútbol')) is None and cd.contexto(dict(p, espn='')) is None
    # no se sabe quién es quién: nada de adivinar
    otro = dict(p, partido='Boston Bruins vs Dallas Stars')
    assert _con_falso(_falso, lambda: cd.contexto(otro, dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc))) is None
    assert _con_falso(lambda u, q=None: None, lambda: cd.contexto(p)) is None         # ESPN caído: nunca lanza


def test_plantillas_con_lo_que_ofrece_playdoit():
    claves = lambda d: {m[0] for m in pl.PLANTILLAS[d]['mercados']}
    assert {'total', 'hand', 'ambos', 'primero', 'prorroga', 'p1total', 'r60'} <= claves('NHL')
    assert {'hand', 'total', 'h1', 'h1total', 'q1total', 'triples', 'asist'} <= claves('NBA') and 'ambos' not in claves('NBA')
    assert {'hand', 'total', 'td', 'fg', 'primero', 'h1total'} <= claves('NFL')
    assert claves('Béisbol') == {'hand', 'total'}                                     # en invierno Playdoit sólo da ganador, hándicap y total
    assert {'hand', 'juegos', 's1'} <= claves('Tenis')
    assert not (claves('NBA') & {'corners', 'tarjetas', 'ambos'})


def test_normaliza_convierte_y_descarta():
    crudo = [{'clave': 'total', 'seleccion': 'mas', 'linea': 5.5, 'prob': .61}, {'clave': 'hand', 'seleccion': 'visita', 'linea': 1.5, 'prob': .7},
             {'clave': 'ambos', 'seleccion': 'si', 'prob': .86}, {'clave': 'r60', 'seleccion': 'empate', 'prob': .22}, {'clave': 'gl', 'seleccion': 'menos', 'linea': 3.5, 'prob': 1.4},
             {'clave': 'corners', 'seleccion': 'mas', 'linea': 9.5, 'prob': .6}, {'clave': 'primero', 'seleccion': 'nadie', 'prob': .1}, {'clave': 'p1total', 'seleccion': 'mas', 'prob': .5}]
    r = pl.normaliza('NHL', crudo, 'Buffalo', 'Columbus')
    por = {x['k']: x for x in r}
    assert por['total']['v'] == 'Más de 5.5' and por['total']['p'] == .61
    assert por['hand']['v'] == 'Columbus +1.5' and por['ambos']['v'] == 'Sí' and por['r60']['v'] == 'Empate'
    assert por['gl']['t'] == 'Goles de Buffalo' and por['gl']['p'] is None             # probabilidad imposible: fuera
    assert 'corners' not in por and 'primero' not in por and 'p1total' not in por      # otro deporte, selección imposible, sin línea
    assert [x['k'] for x in r] == ['total', 'hand', 'r60', 'gl', 'ambos']              # en el orden de la plantilla
    assert pl.normaliza('Fútbol', crudo, 'a', 'b') is None and pl.normaliza('NHL', None, 'a', 'b') is None


def test_la_instruccion_de_cada_deporte():
    import ia_gemini as ia
    nhl, nba = ia.instruccion('NHL'), ia.instruccion('NBA')
    assert '"prorroga"' in nhl and '"p1total"' in nhl and 'MERCADOS DE ESTE DEPORTE' in nhl and 'power play' in nhl
    assert '"triples"' in nba and '"q1total"' in nba and '"prorroga"' in nba and '"p1total"' not in nba
    assert 'promedios_local' in nba
    assert 'MERCADOS DE ESTE DEPORTE' not in ia.instruccion('Fútbol')
    assert 'mercados' in ia.ESQUEMA_GEN['required'] and 'mercados' not in ia.ESQUEMA['required']


def test_la_ia_recibe_el_contexto_y_guarda_los_mercados():
    a = leer('ia_gemini.py')
    assert "'promedios_local': ctx.get('sl')" in a and "plantillas_deporte.normaliza(m.get('deporte', 'Fútbol'), d.get('mercados')" in a
    assert 'add column if not exists mercados jsonb' in leer('supabase', 'v568_ia_mercados.sql')


def test_el_exportador_y_la_pagina():
    assert 'contexto_deportes.contexto(f)' in leer('exportar_web.py')
    w = leer('web', 'app.js')
    assert 'const CTX_DEP = {' in w and "contextoHtml((ps.find((x) => x.ctx) || {}).ctx, L, V, p.liga, p.deporte)" in w
    assert "a.mercados.map((m) => [m.t, m.v, null, m.p])" in w and "(fut || dep === 'NHL')" in w


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
