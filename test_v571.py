"""v571 — tenis y béisbol de invierno con su «Antes del partido» (365Scores); NHL y NBA sin «ambos anotan»; la IA sin el tope de 1000."""
import datetime as dt
import io
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
import contexto_365 as c365
import plantillas_deporte as pl


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _ej(i, gh, ga, tid_h, tid_a, nh='Yo', na='Otro', grupo=4, dia=1):
    return {'id': i, 'startTime': '2026-11-%02dT20:00:00+00:00' % dia, 'statusGroup': grupo, 'homeCompetitor': {'id': tid_h, 'name': nh, 'score': gh},
            'awayCompetitor': {'id': tid_a, 'name': na, 'score': ga}}


def _falso(ruta, **q):
    if ruta == 'games/allscores/':
        return {'games': [{'id': 77, 'startTime': '2026-11-05T23:00:00+00:00', 'homeCompetitor': {'id': 1, 'name': 'Tigres de Aragua'},
                           'awayCompetitor': {'id': 2, 'name': 'Tiburones de La Guaira'}}]}
    if ruta == 'games/results/':
        t = q['competitors']
        return {'games': [_ej(10 + t, 5, 3, t, 9, dia=4), _ej(20 + t, 2, 7, 9, t, dia=3), _ej(30 + t, 1, 0, t, 8, dia=2),
                          _ej(40 + t, -1, -1, t, 8, dia=1), _ej(50 + t, 4, 4, t, 8, grupo=2, dia=4), _ej(60 + t, 9, 9, t, 8, dia=6)]}
    if ruta == 'game/':
        return {'game': {'stages': [{'shortName': str(i), 'homeCompetitorScore': 1.0, 'awayCompetitorScore': 0.0} for i in range(1, 10)] +
                         [{'shortName': 'R', 'homeCompetitorScore': 5.0, 'awayCompetitorScore': 3.0}, {'shortName': 'H', 'homeCompetitorScore': -1.0, 'awayCompetitorScore': -1.0}]}}
    if ruta == 'games/h2h/':
        return {'game': {'h2hGames': [_ej(5, 3, 1, 1, 2, 'Tigres', 'Tiburones', dia=2), _ej(6, 1, 1, 1, 2, 'Tigres', 'Tiburones', dia=9)]}}
    return {}


def _con(f):
    antes = c365._get
    c365._get = _falso
    c365._MEMO.clear()
    try:
        return f()
    finally:
        c365._get = antes


AHORA = dt.datetime(2026, 11, 5, 21, tzinfo=dt.timezone.utc)
BEIS = {'deporte': 'Béisbol', 'partido': 'Aragua vs La Guaira', 'inicio': '2026-11-05 23:00:00'}


def test_nombres_cortos_del_beisbol():
    assert c365.mismo_equipo('Aragua', 'Tigres de Aragua') and c365.mismo_equipo('La Guaira', 'Tiburones de La Guaira')
    assert c365.mismo_equipo('Aguilas de Mexicali', 'Aguilas De Mexicali') and c365.mismo_equipo('Águilas del Zulia', 'Aguilas del Zulia')
    assert not c365.mismo_equipo('Aguilas de Mexicali', 'Águilas del Zulia') and not c365.mismo_equipo('', 'Zulia')


def test_contexto_de_beisbol_sale_de_lo_real():
    c = _con(lambda: c365.contexto(BEIS, None, AHORA))
    # sin lo que no terminó, sin marcador ni lo posterior al pitido
    assert c['sl']['n'] == 3 and c['sl']['gf'] == round((5 + 7 + 1) / 3, 1) and c['fl'] == 'GGG' and len(c['ul']) == 3
    assert c['sl']['pg'] == 1.0 and 'hit' not in c['sl'] and c['ul'][0][5:] == [[1, 0], [3, 0], [5, 0]]
    assert c['h2h'] == [['02/11/26', 'Tigres', '3-1', 'Tiburones']] and c['ts'] == int(AHORA.timestamp())


def test_respeta_nuestro_local_aunque_365_lo_tenga_al_reves():
    m = _con(lambda: c365.partido365(dict(BEIS, partido='La Guaira vs Aragua')))
    assert m['local']['name'] == 'Tiburones de La Guaira' and m['visita']['name'] == 'Tigres de Aragua'
    assert _con(lambda: c365.partido365(dict(BEIS, partido='Magallanes vs Caracas'))) is None
    assert _con(lambda: c365.partido365(dict(BEIS, inicio='2026-11-07 23:00:00'))) is None             # otro día: nada de adivinar


def test_promedios_de_tenis_responden_a_sus_mercados():
    ps = [{'gf': 2.0, 'gc': 1.0, 'lf': [6, 4, 6], 'lc': [4, 6, 3], 's': {'ace': 8, 'df': 2, 'qb': 3, 'pts': .55}, 'c': {'ace': 5}},
          {'gf': 0.0, 'gc': 2.0, 'lf': [3, 2], 'lc': [6, 6], 's': {'ace': 2, 'df': 4, 'qb': 1, 'pts': .4}, 'c': {'ace': 9}}]
    x = c365.promedios_tenis(ps)
    assert x['pg'] == .5 and x['jt'] == (29 + 17) / 2 and x['s1'] == .5 and x['s1j'] == (10 + 9) / 2 and x['s3'] == .5 and x['ace'] == 5
    for k in x:
        assert k == 'n' or k in {f for f in ('pg', 'sf', 'sc', 'jt', 'jf', 'jc', 's1', 's1j', 's3', 'ace', 'df', 'qb', 'pts')}


def test_reutiliza_lo_publicado_y_nunca_lanza():
    previo = {'ts': int(AHORA.timestamp()) - 3600, 'fl': 'GGG'}
    assert c365.contexto(BEIS, previo, AHORA) is previo                                                # vigente: ni una consulta
    viejo = {'ts': int(AHORA.timestamp()) - 8 * 3600, 'fl': 'PPP'}
    assert _con(lambda: c365.contexto(BEIS, viejo, AHORA))['fl'] == 'GGG'
    antes = c365._get
    c365._get = lambda r, **q: None
    c365._MEMO.clear()
    try:
        assert c365.contexto(BEIS, viejo, AHORA) is viejo and c365.contexto(BEIS, None, AHORA) is None  # 365 caído
    finally:
        c365._get = antes
    assert c365.contexto(dict(BEIS, deporte='Fútbol')) is None


FEED = ('SA÷2¬~ZA÷WTA - SINGLES: Cali, clay¬ZEE÷x¬~AA÷a1¬AD÷1793800000¬AB÷3¬AE÷Moyano L.¬AF÷Perez A.¬PX÷p1¬PY÷p2¬AG÷2¬AH÷1¬BA÷6¬BB÷4¬BC÷3¬BD÷6¬BE÷6¬BF÷2¬'
        '~AA÷a2¬AD÷1793800000¬AB÷1¬AE÷Moyano L.¬AF÷Luna B.¬PX÷p1¬PY÷p3¬'
        '~AA÷a3¬AD÷1793700000¬AB÷3¬AE÷Danilova A.¬AF÷Moyano L.¬PX÷p4¬PY÷p1¬AG÷2¬AH÷0¬BA÷6¬BB÷1¬BC÷6¬BD÷0¬'
        '~AA÷a4¬AD÷1793600000¬AB÷3¬AE÷Danilova A.¬AF÷Ruiz C.¬PX÷p4¬PY÷p5¬AG÷0¬AH÷0¬'
        '~ZA÷WTA - DOUBLES: Cali, clay¬~AA÷a5¬AD÷1793800000¬AB÷3¬AE÷Moyano L./Solis P.¬AF÷Ruiz C./Luna B.¬PX÷p7¬PY÷p8¬AG÷2¬AH÷0¬')


def _con_feed(f):
    antes = list(c365._FS)
    c365._FS[:] = c365._feed_tenis(FEED)
    try:
        return f()
    finally:
        c365._FS[:] = antes


def test_el_feed_de_flashscore():
    p = c365._feed_tenis(FEED)
    assert len(p) == 2                                                                                  # sin dobles, sin lo no terminado ni lo no jugado
    assert p[0]['sh'] == [6, 6 - 3, 6] and p[0]['sa'] == [4, 6, 2] and p[1]['gh'] == 2


def test_tenis_itf_sale_de_flashscore():
    fin = dt.datetime.fromtimestamp(1793900000, dt.timezone.utc)
    f = {'deporte': 'Tenis', 'partido': 'Moyano L. vs Danilova A.', 'inicio': fin.strftime('%Y-%m-%d %H:%M:%S')}
    c = _con_feed(lambda: c365._contexto_fs(f, fin, fin))
    assert c['fl'] == 'PG' and c['fv'] == 'G' and c['sl']['n'] == 2 and c['sl']['jt'] == (27 + 13) / 2 and c['sl']['s1'] == .5
    assert c['ul'][0][1] == 'Perez A.' and c['ul'][0][5:7] == [[15, 12], [6, 4]] and c['ul'][1][5:7] == [[1, 12], [1, 6]]
    assert c['h2h'] == [[dt.datetime.fromtimestamp(1793700000, dt.timezone.utc).strftime('%d/%m/%y'), 'Danilova A.', '2-0', 'Moyano L.']]
    # nada posterior al pitido
    tem = dt.datetime.fromtimestamp(1793750000, dt.timezone.utc)
    assert _con_feed(lambda: c365.historial_fs('Moyano L.', tem))[0]['nrival'] == 'Danilova A.'
    # dos tenistas distintos con el mismo nombre: nada de adivinar
    doble = FEED + '~ZA÷ITF¬~AA÷a9¬AD÷1793800000¬AB÷3¬AE÷Moyano L.¬AF÷Otra Z.¬PX÷p99¬PY÷p98¬AG÷2¬AH÷0¬BA÷6¬BB÷1¬BC÷6¬BD÷0¬'
    antes = list(c365._FS)
    c365._FS[:] = c365._feed_tenis(doble)
    try:
        assert c365.historial_fs('Moyano L.', fin) == []
    finally:
        c365._FS[:] = antes


def test_ya_jugado_no_se_calcula():
    assert c365.contexto(BEIS, None, AHORA + dt.timedelta(days=2)) is None


def test_las_plantillas_tienen_lo_que_ofrece_playdoit():
    cl = lambda d: {m[0] for m in pl.PLANTILLAS[d]['mercados']}
    assert 'ambos' not in cl('NHL') and 'ambos' not in cl('NBA') and 'ambos' not in cl('NFL') and 'ambos' not in cl('Béisbol')
    assert {'hand', 'hjuegos', 'juegos', 'jl', 'jv', 's1', 's1juegos', 'ambos', 'aces', 'breaks', 'df'} <= cl('Tenis')
    assert cl('Béisbol') == {'hand', 'total'} and 'h15' in pl.PLANTILLAS['Béisbol']['guia'] and 'qb=quiebres' in pl.PLANTILLAS['Tenis']['guia']


def test_la_instruccion_de_la_nhl_no_pide_ambos():
    import ia_gemini as ia
    nhl = ia.instruccion('NHL')
    assert 'Ambos anotan' not in nhl and 'AMBOS' not in nhl and 'ambos_anotan' not in nhl and 'primero_anota' in nhl


def test_la_ia_lee_por_paginas_y_rehace_con_prudencia():
    import ia_gemini as ia
    a = leer('ia_gemini.py')
    assert "'limit': 1000, 'offset': i * 1000" in a and "'limit': 5000" not in a
    ahora = dt.datetime(2026, 11, 5, 20, tzinfo=dt.timezone.utc)
    base = {'deporte': 'NHL', 'ctx': {'fl': 'G'}, 'inicio': '2026-11-05 23:00:00'}
    ia.CON_MERCADOS.clear()
    ia.CON_MERCADOS.add('listo')
    lista = [dict(base, id='viejo'), dict(base, id='listo'), dict(base, id='nuevo'), dict(base, id='sinctx', ctx=None),
             dict(base, id='lejos', inicio='2026-11-08 23:00:00'), dict(base, id='futbol', deporte='Fútbol')]
    r = ia.por_rehacer(lista, {'viejo', 'listo', 'sinctx', 'lejos', 'futbol'}, ahora)
    assert [m['id'] for m in r] == ['viejo']
    ia.CON_MERCADOS.clear()


def test_la_pagina():
    w = leer('web', 'app.js')
    assert "a.btts && fut ? ['🎯 Ambos anotan'," in w and "['ambos', 'Ambos marcan', pc100]" not in w
    assert "'Béisbol': { u: ['1.ª entr.', '3 entr.', '5 entr.']" in w and "Tenis: { u: ['Juegos', '1.er set', 'Aces']" in w
    assert "DEP_ICO[dep] || 'ball-football'" in w                                                      # un partido de béisbol sin escudo no lleva balón de futbol


def test_el_exportador_y_los_escudos():
    e, s = leer('exportar_web.py'), leer('escudos.py')
    assert e.index('espn_vivo.emparejar(') < e.index('contexto_365.contexto(f, previo.get(k))') and 'contexto_365.publicados()' in e
    assert "'Fútbol', 'Tenis', 'Béisbol'" in s and 'buscar_365(f.get(\'partido\'), f.get(\'inicio\'), cache, dep)' in s


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
