"""v563 — Telegram: la foto es un parley que se puede ganar; en el gratis sólo se esconde la jugada; y al cumplirse, foto de «¡ganamos!»."""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarjeta_tg as t
import telegram_canales as tc

AHORA = dt.datetime(2026, 11, 5, 18, 0, tzinfo=dt.timezone.utc)


def pick(i, partido=None, estado='pendiente', cuota=1.2, prob=.92, nivel='Diamante'):
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


# ---------- v564 ----------
def met(fam, lado, dire, lin, cuota, casa, score, completa=1):
    return [fam, lado, dire, lin, cuota, casa, score, 18, 20, 9, 10, 0, 9, completa, 3.1]


def test_gratis_solo_oro():
    ini = (AHORA + dt.timedelta(hours=2)).isoformat()
    oro = dict(pick(1, cuota=1.30, prob=.75), elige=False, inicio=ini)
    plata = dict(pick(2, cuota=1.15, prob=.75), elige=False, inicio=ini)
    plat = dict(pick(3, cuota=1.20, prob=.85), elige=False, inicio=ini)
    assert [p['id'] for p in tc.candidatas_gratis([oro, plata, plat], AHORA)] == ['p1']


def test_vip_cualquier_nivel_y_solo_lo_mostrado_lleva_texto():
    tc._TICKETS.clear()
    ps = [dict(pick(i, cuota=1.30, prob=.75), elige=False) for i in range(1, 10)]        # todos Oro
    lote = [x for x in tc.armar_vip(ps, set(), AHORA) if x[0] and 'hora de apostar' in x[0]]
    assert lote, 'el VIP también manda Oro'
    con_texto = [f for f in lote[-1][1] if f[2] == 'pick' and len(f) > 3]
    sin_texto = [f for f in lote[-1][1] if f[2] == 'pick' and len(f) == 3]
    assert len(con_texto) == tc.MAX_VIP_MSG and len(sin_texto) == 3


def test_resultados_vip_solo_de_lo_mandado():
    fin = [dict(pick(1), estado='verde'), dict(pick(2), estado='verde')]
    r = [x for x in tc.armar_vip(fin, {('p1', 'vip', 'pick')}, AHORA) if x[0] and 'Resultados VIP' in x[0]]
    assert len(r) == 1 and r[0][1] == [('p1', 'vip', 'resultado')]


def test_parley_solo_de_alta_probabilidad():
    ps = [pick(1, prob=.9), pick(2, prob=.85), pick(3, prob=.84)]
    assert [p['id'] for p in tc.parley_de(ps)] == ['p1', 'p2']              # con la 3.ª bajaría a 65 %−
    assert [p['id'] for p in tc.parley_de([pick(1, prob=.92), pick(2, prob=.9), pick(3, prob=.88)])] == ['p1', 'p2', 'p3']
    assert [p['id'] for p in tc.parley_de([pick(1, prob=.7), pick(2, prob=.7)])] == ['p1']   # individual
    assert tc.parley_de([pick(1, prob=.6)]) == []                           # ni la mejor llega: sin foto
    lote = [x for x in tc.armar_vip([pick(1, prob=.6)], set(), AHORA) if x[0] and 'hora de apostar' in x[0]][-1]
    assert lote[2] is None and not [f for f in lote[1] if f[2] == 'ticket']


def test_patas_del_metodo():
    bien = [met('goles', 't', 'menos', 4.5, 1.15, .86, .97), met('corners', 'a', 'mas', 2.5, 1.2, .8, .91), met('tarjetas', 't', 'menos', 5.5, 1.29, .74, .85),
            met('goles', 'h', 'mas', .5, 1.2, .8, .96)]
    assert [x[0] for x in tc.elegir_patas_metodo(bien)] == ['goles', 'corners']                   # 2 patas, una por estadística
    # los remates totales no entran, ni lo de poca historia, ni lo de menos de 80 %
    assert tc.elegir_patas_metodo([met('remates', 'h', 'mas', 9.5, 1.3, .85, .95), met('goles', 't', 'mas', 1.5, 1.3, .85, .95, 0), met('corners', 't', 'mas', 7.5, 1.3, .85, .79)]) is None
    # baja probabilidad conjunta: no
    assert tc.elegir_patas_metodo([met('goles', 't', 'menos', 4.5, 1.25, .77, .97), met('corners', 'a', 'mas', 2.5, 1.43, .66, .91)]) is None
    # cuota de menos de 1,25: no
    assert tc.elegir_patas_metodo([met('goles', 't', 'menos', 4.5, 1.1, .9, .97), met('corners', 'a', 'mas', 2.5, 1.1, .9, .91)]) is None


def _partido_metodo():
    p = dict(pick(1), espn='soccer/all:123', partido='Benfica vs Lech')
    m = [met('goles', 't', 'menos', 4.5, 1.15, .86, .97), met('corners', 'a', 'mas', 2.5, 1.2, .8, .91)]
    return p, m


def test_armar_metodo_una_vez_y_con_tope():
    tc._TICKETS.clear()
    p, m = _partido_metodo()
    r = tc.armar_metodo([p], set(), AHORA, {'p1': {'met': m}})
    assert len(r) == 1 and 'Corners' not in r[0][0] and 'Córners de Lech: <b>' not in r[0][0] and 'Córners de Lech: más de 2.5' in r[0][0]
    assert '~1.38' in r[0][0] and '~69 %' in r[0][0] and r[0][2][:4] == b'\x89PNG'
    # la publicidad en el gratis: partido y cuota, sin la jugada
    tz = tc.teaser_metodo(r, AHORA)
    assert len(tz) == 1 and 'Benfica vs Lech' in tz[0][0] and '~1.38' in tz[0][0] and 'Córners' not in tz[0][0] and 'Goles' not in tz[0][0]
    assert 'hazte VIP' in tz[0][0] and tz[0][1][0][1:] == ('gratis', 'teaser') and tz[0][2][:4] == b'\x89PNG'
    k = r[0][1][0]
    assert k[2] == 'metodo' and tc.armar_metodo([p], {k}, AHORA, {'p1': {'met': m}}) == []
    hoy = AHORA.astimezone(tc.CDMX).strftime('%Y-%m-%d')
    tope = {('metodo:x%d|%s' % (i, hoy), 'vip', 'metodo') for i in range(tc.METODO_MAX_DIA)}
    assert tc.armar_metodo([p], tope, AHORA, {'p1': {'met': m}}) == []
    # ya empezó o falta mucho: nada
    assert tc.armar_metodo([dict(p, inicio=(AHORA + dt.timedelta(hours=9)).isoformat())], set(), AHORA, {'p1': {'met': m}}) == []


def _registra_metodo():
    tc._TICKETS.clear()
    p, m = _partido_metodo()
    r = tc.armar_metodo([p], set(), AHORA, {'p1': {'met': m}})
    f = [x for x in r[0][1] if x[2] == 'ticket'][0]
    tc._TICKETS[(f[0], f[1])] = f[3]
    return f[0]


def test_ganado_del_metodo_con_datos_reales():
    k = _registra_metodo()
    despues = AHORA + dt.timedelta(hours=5)
    bueno = {'goals': (2, 0), 'corners': (5, 3), 'tarjetas': (1, 1)}       # 2 goles < 4,5 · Lech 3 córners > 2,5
    g = tc.armar_ganados([], set(), despues, lambda *a: bueno)
    assert len(g['vip']) == 1 and len(g['gratis']) == 1 and g['vip'][0][2][:4] == b'\x89PNG'
    assert '~1.38' in g['vip'][0][0] and '~+' in g['vip'][0][0] and 'VIP antes del partido' in g['gratis'][0][0]
    # no se pregunta antes de tiempo
    llamadas = []
    assert tc.armar_ganados([], set(), AHORA, lambda *a: llamadas.append(a))['vip'] == [] and not llamadas
    # y ya avisado, no se repite
    assert tc.armar_ganados([], {(k, 'vip', 'ganado'), (k, 'gratis', 'ganado')}, despues, lambda *a: bueno) == {'vip': [], 'gratis': []}


def test_el_metodo_no_cumplido_o_sin_datos_no_da_foto():
    k = _registra_metodo()
    despues = AHORA + dt.timedelta(hours=5)
    g = tc.armar_ganados([], set(), despues, lambda *a: {'goals': (2, 0), 'corners': (5, 1)})    # Lech 1 córner
    assert g['gratis'] == [] and g['vip'] == [('', [(k, 'vip', 'ganado'), (k, 'gratis', 'ganado')])]
    # falta la estadística: se espera; a las 48 h se cierra sin foto
    assert tc.armar_ganados([], set(), despues, lambda *a: {'goals': (2, 0)}) == {'vip': [], 'gratis': []}
    assert tc.armar_ganados([], set(), despues, lambda *a: None) == {'vip': [], 'gratis': []}
    tarde = tc.armar_ganados([], set(), AHORA + dt.timedelta(hours=60), lambda *a: None)
    assert tarde['vip'] == [('', [(k, 'vip', 'ganado'), (k, 'gratis', 'ganado')])]


class _Resp:
    def __init__(self, d):
        self.d = d

    def json(self):
        return self.d


def _espn(nombre, completed=True, state='post', local='Benfica', visita='Lech', gl=2, gv=1):
    equipos = [{'team': {'id': '1'}, 'statistics': [{'name': 'wonCorners', 'displayValue': '7'}, {'name': 'yellowCards', 'displayValue': '2'}, {'name': 'redCards', 'displayValue': '1'}, {'name': 'shotsOnTarget', 'displayValue': '6'}]},
               {'team': {'id': '2'}, 'statistics': [{'name': 'wonCorners', 'displayValue': '3'}, {'name': 'yellowCards', 'displayValue': '1'}, {'name': 'redCards', 'displayValue': '0'}, {'name': 'shotsOnTarget', 'displayValue': '2'}]}]
    return {'header': {'competitions': [{'status': {'type': {'name': nombre, 'completed': completed, 'state': state}},
                                         'competitors': [{'homeAway': 'home', 'score': str(gl), 'team': {'id': '1', 'displayName': local}},
                                                         {'homeAway': 'away', 'score': str(gv), 'team': {'id': '2', 'displayName': visita}}]}]},
            'boxscore': {'teams': equipos}}


def _con_espn(d, a='Benfica', b='Lech'):
    import requests
    original = requests.get
    requests.get = lambda *x, **k: _Resp(d)
    try:
        return tc._final_espn('soccer/all:1', a, b)
    finally:
        requests.get = original


def test_final_espn_no_da_por_jugado_lo_pospuesto():
    # el caso real: Unión La Calera vs Coquimbo, pospuesto: state «post», 0-0
    for nombre, completed, state in (('STATUS_POSTPONED', False, 'post'), ('STATUS_CANCELED', False, 'post'), ('STATUS_ABANDONED', False, 'post'), ('STATUS_SCHEDULED', False, 'pre'), ('STATUS_SECOND_HALF', False, 'in')):
        assert _con_espn(_espn(nombre, completed, state, gl=0, gv=0)) is None, nombre
    assert _con_espn(_espn('STATUS_FINAL_AET')) is None                   # prórroga: la casa paga a los 90'


def test_final_espn_y_el_lado_de_cada_equipo():
    f = _con_espn(_espn('STATUS_FULL_TIME'))
    assert f == {'goals': (2, 1), 'corners': (7, 3), 'tarjetas': (3, 1), 'shots_on': (6, 2)}
    # nuestro partido lo escribe al revés que ESPN
    f = _con_espn(_espn('STATUS_FULL_TIME'), 'Lech', 'Benfica')
    assert f == {'goals': (1, 2), 'corners': (3, 7), 'tarjetas': (1, 3), 'shots_on': (2, 6)}
    assert _con_espn(_espn('STATUS_FULL_TIME'), 'Otro', 'Distinto') is None   # no se sabe quién es quién


def test_liquidar_no_cierra_lo_pospuesto():
    import liquidar_pendientes as lq

    class S:
        def __init__(self, d):
            self.d = d

        def get(self, *a, **k):
            return _Resp(self.d)
    assert lq._espn('soccer/all:1', 'Benfica', 'Lech', S(_espn('STATUS_POSTPONED', False, 'post', gl=0, gv=0))) is None
    assert lq._espn('soccer/all:1', 'Benfica', 'Lech', S(_espn('STATUS_FULL_TIME')))['g'] == (2, 1)


def test_pospuesto_abierto_hasta_que_se_juegue():
    """v565 — el mismo pick: mientras esté pospuesto no se toca; jugado, se liquida con su marcador real, aunque pasen semanas."""
    import liquidar_pendientes as lq
    ini = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=20)).isoformat()
    fila = {'id': 'x1', 'partido': 'Benfica vs Lech', 'apuesta': 'Gana Lech', 'deporte': 'Fútbol', 'inicio': ini, 'fecha': ini[:10], 'espn': 'soccer/all:1', 'tipo': 'pick'}

    class S:
        def __init__(self, espn):
            self.espn, self.parches, self.params = espn, [], None

        def get(self, url, **k):
            if url.endswith('/picks'):
                self.params = k.get('params')
                return type('R', (), {'ok': True, 'json': lambda s: [dict(fila)]})()
            if url.endswith('/picks_premium'):
                return type('R', (), {'ok': True, 'json': lambda s: []})()
            if 'espn' in url:
                return _Resp(self.espn)
            raise RuntimeError('sin feed en la prueba')

        def patch(self, url, **k):
            self.parches.append(k['json'])
            return type('R', (), {'ok': True})()
    s = S(_espn('STATUS_POSTPONED', False, 'post', gl=0, gv=0))
    assert lq.cerrar([], 'http://x', 'k', s) == 0 and s.parches == []
    # 20 días después sigue en la lista que se revisa (antes eran 15)
    corte = dt.datetime.fromisoformat(s.params['inicio'].replace('gte.', ''))
    assert (dt.datetime.now(dt.timezone.utc) - corte).days >= lq.DIAS_POSPUESTO - 1 and lq.DIAS_POSPUESTO >= 45
    s = S(_espn('STATUS_FULL_TIME', gl=0, gv=2))
    locales = [dict(fila, estado='pendiente')]
    assert lq.cerrar(locales, 'http://x', 'k', s) == 1
    assert s.parches[0]['estado'] == 'verde' and s.parches[0]['marcador'] == '0-2' and locales[0]['estado'] == 'verde'


def test_lo_enviado_se_lee_completo():
    """v566 — Supabase da 1000 filas por vez: lo recién mandado debe verse aunque haya miles, o se manda otra vez."""
    import requests
    filas = [{'pick': 'p%d' % i, 'canal': 'vip', 'tipo': 'pick', 'texto': 't'} for i in range(2500)]
    pedidos = []

    def falso(url, headers=None, timeout=None, params=None):
        pedidos.append(params)
        o, n = params['offset'], min(params['limit'], 1000)
        return type('R', (), {'ok': True, 'status_code': 200, 'json': lambda s: filas[o:o + n]})()
    antes, env = requests.get, dict(os.environ)
    requests.get = falso
    os.environ.update({'SUPABASE_URL': 'http://x', 'SUPABASE_SERVICE_KEY': 'k'})
    try:
        vistos = tc.ya_enviados()
        assert len(vistos) == 2500 and ('p2499', 'vip', 'pick') in vistos and len(pedidos) == 3
        assert 'enviado.desc' in pedidos[0]['order']
        # si falla a media lectura no se sabe qué se mandó: no se manda nada
        requests.get = lambda *a, **k: type('R', (), {'ok': False, 'status_code': 500})()
        assert tc.ya_enviados() is None
    finally:
        requests.get = antes
        os.environ.clear()
        os.environ.update(env)


def test_cumplio_pata():
    f = {'corners': (5, 3), 'goals': (2, 0)}
    assert tc.cumplio_pata({'fam': 'corners', 'lado': 'h', 'dir': 'mas', 'linea': 4.5}, f) is True
    assert tc.cumplio_pata({'fam': 'corners', 'lado': 'a', 'dir': 'mas', 'linea': 4.5}, f) is False
    assert tc.cumplio_pata({'fam': 'corners', 'lado': 't', 'dir': 'menos', 'linea': 8.5}, f) is True
    assert tc.cumplio_pata({'fam': 'tarjetas', 'lado': 't', 'dir': 'menos', 'linea': 8.5}, f) is None


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
