# -*- coding: utf-8 -*-
"""v588 — la calificación de la IA no se atasca, y el experimento es de verdad a ciegas."""
import io
import json
import os

import ia_experimento as ex

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _a(**k):
    d = {'fecha': '2026-10-20', 'partido': 'A vs B', 'liga': 'L', 'deporte': 'Fútbol', 'noticias': 'n1 | n2', 'creado': '2026-10-19T10:00:00+00:00', 'inicio': '2026-10-20 18:00:00+00'}
    d.update(k)
    return d


PICKS = [{'id': 'p1', 'fecha': '2026-10-20', 'partido': 'A vs B', 'apuesta': '🔒 Pick', 'estado': 'verde', 'tipo': 'pick', 'cuota': 1.2, 'prob': .8, 'marcador': '2-1'}]


def test_entrada_a_ciegas():
    lista = ex.partidos_a_preguntar([_a()], PICKS, {'p1': 'Gana A'}, set())
    assert lista[0]['apuestas'] == ['Gana A']
    t = json.dumps(ex.entrada(lista), ensure_ascii=False).lower()
    for prohibido in ['cuota', 'prob', 'verde', 'roja', 'marcador', 'nivel', 'estado', '1.2', '2-1', 'lock', '🔒']:
        assert prohibido not in t, prohibido


def test_solo_noticias_anteriores_al_partido():
    assert ex.partidos_a_preguntar([_a(creado='2026-10-20T19:00:00+00:00')], PICKS, {'p1': 'Gana A'}, set()) == []
    assert ex.partidos_a_preguntar([_a(noticias=None)], PICKS, {'p1': 'Gana A'}, set()) == []


def test_premium_sin_texto_real_o_ya_hecho_no_entra():
    assert ex.partidos_a_preguntar([_a()], PICKS, {}, set()) == []
    assert ex.partidos_a_preguntar([_a()], PICKS, {'p1': 'Gana A'}, {('2026-10-20', 'A vs B', 'Gana A')}) == []
    pendiente = [dict(PICKS[0], estado='pendiente')]
    assert ex.partidos_a_preguntar([_a()], pendiente, {'p1': 'Gana A'}, set()) == []     # lo que aún no se juega no se toca


def test_respuesta_valida():
    lote = [{'fecha': 'f', 'partido': 'A vs B', 'apuestas': ['Gana A']}]
    f = ex.filas_de_respuesta(lote, [{'i': 0, 'j': 0, 'impacto': -2, 'factores': ['baja_clave_favorecido', 'inventado'], 'nota': 'x'},
                                     {'i': 9, 'j': 0, 'impacto': 1}, {'i': 0, 'j': 0, 'impacto': 9}])
    assert len(f) == 1 and f[0]['impacto'] == -2 and f[0]['factores'] == ['baja_clave_favorecido']


def test_instruccion_no_ancla_al_mercado():
    i = ex.INSTRUCCION.lower()
    assert 'no conoces cuotas' in i and 'mercado' not in i


def test_flujo_manual_y_tabla_privada():
    y = leer('.github', 'workflows', 'ia_experimento.yml')
    assert 'workflow_dispatch' in y and 'schedule' not in y
    s = leer('supabase', 'v588_ia_experimento.sql')
    assert 'revoke all on table public.ia_experimento from public, anon, authenticated' in s and 'row level security' in s


def test_calificacion_no_se_atasca():
    a = leer('ia_gemini.py')
    assert "'order': 'inicio.desc'" in a and "'offset': pagina * 300" in a and 'TOPE_EVALUAR_S' in a
    assert 'picks = picks + _picks_de_la_base(sb, desde[:10])' in a


def test_vivo_a_ciegas():
    m = {'fecha': '2026-11-07', 'partido': 'A vs B', 'liga': 'L', 'deporte': 'NBA', 'bajas': {'home': ['X (Out): rodilla']}, 'titulares': ['t'], 'apuestas': ['Gana A'],
         'cuota': 1.2, 'prob': .8, 'nivel': 'Diamante', 'ini': 'x'}
    t = json.dumps(ex.entrada_vivo(m), ensure_ascii=False).lower()
    for prohibido in ['cuota', 'prob', 'diamante', 'nivel', '1.2']:
        assert prohibido not in t, prohibido


def test_bajas_por_nombre_exacto():
    tabla = {'mls|Inter Miami|Toronto': {'home': {'bajas': [{'jugador': 'J', 'tipo': 'injury'}]}, 'away': {'bajas': []}}}
    assert ex.bajas_fotmob('Inter Miami vs Toronto', tabla)['home'] == ['J (injury)']
    assert ex.bajas_fotmob('Inter vs Toronto', tabla) == {}


def test_vivo_no_cambia_picks_y_no_quita_cupo():
    a = leer('ia_experimento.py')
    assert 'CUPO_VIVO = 300' in a and "not ahora < ini <= ahora + dt.timedelta(hours=HORAS_VIVO)" in a
    y = leer('.github', 'workflows', 'sitio_web.yml')
    assert 'python ia_experimento.py --vivo' in y and y.index('name: IA (Gemini)') < y.index('ia_experimento.py --vivo')
    i = y.index('ia_experimento.py --vivo')
    assert 'continue-on-error: true' in y[i - 400:i]
    assert 'add column if not exists datos' in leer('supabase', 'v589_ia_experimento_datos.sql')


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
