"""v572 — el cupo de Gemini: 429 por minuto o por día, tope de tiempo y el Pulso contado y con freno."""
import io
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
import ia_gemini as ia


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


class R:
    def __init__(self, status, cuerpo):
        self.status_code, self._c = status, cuerpo
        self.ok = status < 400
        self.text = str(cuerpo)

    def json(self):
        if self._c is None:
            raise ValueError()
        return self._c


def _429(qid, valor='15', espera='7s'):
    return R(429, {'error': {'details': [{'violations': [{'quotaId': qid, 'quotaValue': valor}]}, {'retryDelay': espera}]}})


def test_distingue_minuto_de_dia():
    d, e, t = ia.razon_429(_429('GenerateRequestsPerMinutePerProjectPerModel-FreeTier'))
    assert d is False and e == 7 and 'PerMinute' in t and '=15' in t
    d, _, t = ia.razon_429(_429('GenerateRequestsPerDayPerProjectPerModel-FreeTier', '1000'))
    assert d is True and '=1000' in t
    assert ia.razon_429(R(429, None))[0] is True and ia.razon_429(R(429, {'error': {}}))[0] is True      # si no se entiende, como siempre


def _con_respuestas(respuestas):
    import requests
    import time as _t
    antes, dormir, env = requests.post, _t.sleep, os.environ.get('GEMINI_API_KEY')
    siguiente = iter(respuestas)
    pausas = []
    requests.post = lambda *a, **k: next(siguiente)
    _t.sleep = pausas.append
    os.environ['GEMINI_API_KEY'] = 'x'
    ia._AGOTADOS.clear()
    ia.USO.clear()
    try:
        return ia.preguntar([{'partido': 'A vs B'}], 'NHL', 'analisis', ['lite']), pausas
    finally:
        requests.post, _t.sleep = antes, dormir
        if env is None:
            del os.environ['GEMINI_API_KEY']
        else:
            os.environ['GEMINI_API_KEY'] = env


def test_por_minuto_espera_y_no_gasta_el_dia():
    bien = R(200, {'candidates': [{'content': {'parts': [{'text': '{"partidos": [{"partido": "A vs B"}]}'}]}}]})
    r, pausas = _con_respuestas([_429('GenerateRequestsPerMinutePerProjectPerModel-FreeTier'), bien])
    assert r['A vs B']['_modelo'] == 'lite' and pausas == [8.0] and 'lite' not in ia._AGOTADOS
    assert ia.USO[('lite', 'analisis')]['agotado'] is False


def test_por_dia_marca_el_modelo():
    r, pausas = _con_respuestas([_429('GenerateRequestsPerDayPerProjectPerModel-FreeTier', '1000', '40000s')])
    assert not pausas and 'lite' in ia._AGOTADOS and ia.USO[('lite', 'analisis')]['agotado'] is True
    ia._AGOTADOS.clear()


def test_por_minuto_repetido_no_marca_agotado():
    q = 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier'
    r, pausas = _con_respuestas([_429(q), _429(q), _429(q)])
    assert r is None and len(pausas) == 2 and 'lite' not in ia._AGOTADOS and ia.USO[('lite', 'analisis')]['agotado'] is False


def test_la_pasada_para_a_tiempo():
    a = leer('ia_gemini.py')
    assert 'TOPE_PASADA_S = 480' in a and 'MAX_SIN_RESPUESTA = 3' in a and 'sin_respuesta = 0 if filas else sin_respuesta + 1' in a
    assert a.index('time.monotonic() - inicio > TOPE_PASADA_S') < a.index('web = noticias_rss(lote)')


def test_el_presupuesto_del_dia():
    a = leer('ia_gemini.py')
    assert 'CUPO_SOLO = 250' in a and 'CUPO_PICKS = 460' in a and "if gastado >= (CUPO_PICKS if con_pick and not ventana else CUPO_SOLO):" in a
    assert a.index('gastado = USADAS_HOY') < a.index('web = noticias_rss(lote)')
    import datetime as dt
    import requests
    antes = requests.get
    requests.get = lambda *x, **k: R(200, [{'modelo': ia.MODELO_CUPO, 'llamadas': 100}, {'modelo': ia.MODELO_CUPO, 'llamadas': 40}, {'modelo': 'gemini-flash-latest', 'llamadas': 20}])
    try:
        assert ia.leer_uso_de_hoy(('https://x/ia_analisis', {}), dt.datetime(2026, 11, 5, tzinfo=dt.timezone.utc)) == 140
    finally:
        requests.get = antes
        ia.USADAS_HOY['lite'] = 0


def test_el_pulso_cuenta_y_frena():
    p = leer('supabase', 'functions', 'pulso-vivo', 'index.ts')
    assert "const MODELOS_IA = ['gemini-flash-lite-latest', 'gemini-flash-latest'];" in p and "tipo: 'pulso'" in p and 'USO_IA.llamadas++;' in p
    assert '!ms.length || USO_IA.pausa) return null;' in p and 'await leerPausaIA();' in p and 'await guardarUsoIA();' in p
    assert p.index('if (r.status === 429) {') < p.index('if (!r.ok) continue;')
    assert 'if (r.status >= 500) { USO_IA.pausa = true; return null; }' in p and 'const TOPE_PULSO_DIA = 240;' in p


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
