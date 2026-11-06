# -*- coding: utf-8 -*-
"""v583 — lo que quedó de la IA en español en la app en inglés, y los picks de hoy sin análisis."""
import datetime as dt
import io
import os

import ia_gemini as ia

RAIZ = os.path.dirname(os.path.abspath(__file__))
AHORA = dt.datetime(2026, 11, 6, 14, 0, tzinfo=dt.timezone.utc)


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _m(inicio, peso=1, deporte='NHL'):
    return {'partido': 'A vs B', 'inicio': inicio, 'peso': peso, 'deporte': deporte}


def test_lo_de_hoy_va_antes_que_lo_lejano():
    hoy_menor, lejos_menor = _m('2026-11-06 17:30:00+00:00', deporte='Tenis'), _m('2026-11-08 17:30:00+00:00', deporte='Tenis')
    solo = _m('2026-11-06 17:30:00+00:00', peso=-1, deporte='Tenis')
    principal_lejos = dict(_m('2026-11-08 17:30:00+00:00'), deporte=next(iter(ia.PRINCIPAL_OTROS)))
    t = lambda m: ia.turno(m, {}, AHORA)
    assert t(hoy_menor) == 0
    assert t(principal_lejos) == 1
    assert t(lejos_menor) == 2
    assert t(solo) == 3


def test_un_diamante_de_hoy_entra_antes_que_una_liga_principal_lejana():
    orden = sorted([dict(_m('2026-11-08 17:30:00+00:00'), deporte=next(iter(ia.PRINCIPAL_OTROS))), _m('2026-11-06 17:30:00+00:00', deporte='Tenis')],
                   key=lambda m: ia.turno(m, {}, AHORA))
    assert orden[0]['deporte'] == 'Tenis'


def test_traduccion_completa():
    x = {'analisis': 'Hola', 'veredictos': [{'apuesta': 'a', 'motivo': 'uno', 'estado': 'verde'}], 'noticias': 'n1 | n2'}
    c = ia.cambio_traducido(x, {'analisis_en': ' Hello ', 'motivos_en': ['one'], 'noticias_en': ['a', 'b']})
    assert c['analisis_en'] == 'Hello' and c['noticias_en'] == 'a | b'
    assert c['veredictos'] == [{'apuesta': 'a', 'motivo': 'uno', 'estado': 'verde', 'motivo_en': 'one'}]   # no pierde lo demás


def test_largo_distinto_no_se_usa():
    x = {'analisis': 'Hola', 'veredictos': [{'motivo': 'uno'}, {'motivo': 'dos'}], 'noticias': 'n1 | n2'}
    c = ia.cambio_traducido(x, {'analisis_en': 'Hello', 'motivos_en': ['one'], 'noticias_en': ['a']})
    assert c == {'analisis_en': 'Hello'}


def test_lo_ya_traducido_no_se_pisa():
    x = {'analisis': 'Hola', 'analisis_en': 'Bueno', 'veredictos': [{'motivo': 'uno', 'motivo_en': 'first'}], 'noticias': ''}
    c = ia.cambio_traducido(x, {'analisis_en': '', 'motivos_en': ['otro'], 'noticias_en': []})
    assert 'analisis_en' not in c and c['veredictos'][0]['motivo_en'] == 'first'


def test_lo_ya_en_ingles_no_se_vuelve_a_mandar():
    e = ia._entrada_traducir([{'analisis': 'Hola', 'analisis_en': 'Hi', 'noticias': 'n1 | n2', 'veredictos': None}])[0]
    assert e['analisis'] == '' and e['noticias'] == ['n1', 'n2'] and e['motivos'] == []


def test_ventanas_no_mandan_columna_que_no_existe():
    a = leer('ia_gemini.py')
    assert "f.pop('analisis_en', None)" in a
    assert a.index("f['base'], f['id'], f['ventana']") < a.index("f.pop('analisis_en', None)")


def test_analisis_con_lite_primero():
    assert 'res = preguntar(entrada, dep, tipo, LITE)' in leer('ia_gemini.py')


def test_app_usa_lo_traducido():
    a = leer('web', 'app.js')
    assert "(window.I18N.lang === 'en' && a.noticias_en) || a.noticias" in a
    assert "(window.I18N.lang === 'en' && ia.rec.motivo_en) || ia.rec.motivo" in a
    assert a.count("(window.I18N.lang === 'en' && v.motivo_en) || v.motivo") == 2
    assert 'motivo_en' in leer('web', 'cuenta.js')
    assert "[/^[Gg]ana (.+)$/, '$1 to win']" in leer('web', 'idioma.js')     # «La IA ve: gana Barracas Central»


def test_pulso_y_migracion():
    assert "required: ['mercado', 'motivo', 'motivo_en']" in leer('supabase', 'functions', 'pulso-vivo', 'index.ts')
    s = leer('supabase', 'v583_ia_noticias_en.sql')
    assert 'ia_analisis add column if not exists noticias_en' in s and 'pulso_ia add column if not exists motivo_en' in s


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
