"""v545-v546 — el Oro con más cuota (70-79 %, cuota ≥ 1,25) igual en la página y la base; Mis picks plegable con historial
por periodo; los partidos que sigues se reconocen; el morado de la IA en la lista; el Platino ya no es violeta."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_oro_igual_en_pagina_y_base():
    a, s = leer('web', 'app.js'), leer('supabase', 'v545_oro_mas_cuota.sql')
    assert "if ((p.prob || 0) >= 0.70 && Number(p.cuota || 0) >= 1.25) return { n: 'Oro'" in a
    assert "when coalesce(p_prob, 0) >= 0.70 and coalesce(p_cuota, 0) >= 1.25 then 'Oro'" in s
    assert "public.nivel_pick((p).tipo, (p).elige, (p).prob, (p).cuota) = 'Oro' then 0" in s   # el Oro es lo gratis


def test_mis_picks_plegable_y_por_periodo():
    c, h = leer('web', 'cuenta.js'), leer('web', 'index.html')
    assert 'data-plegar="mis-comb"' in h and 'data-plegar="mi-hist"' in h
    assert "[[1, 'Día'], [7, 'Semana'], [30, 'Mes'], [365, 'Año'], [0, 'Todo']]" in c
    assert 'data-hist-dia=' in c and "localStorage.setItem('sp_plegado'" in c


def test_partidos_que_sigo_y_morado_en_la_lista():
    a, css = leer('web', 'app.js'), leer('web', 'estilo.css')
    assert "'<span class=\"pf-sigo\">★ Lo sigues</span>'" in a and '.partido-fila.sigo {' in css
    assert "al.has(claveNombre(p))" in a                                  # la campana 🔔 también cuenta en Mis picks
    assert "const ia = Math.max(0, ...ps.map((x) => iaSegura(x)));" in a and '.partido-fila.ia-2 .pf {' in css
    assert css.rstrip().count(':root { --platino: #f472b6; }') == 1        # Platino en rosa, no violeta como la IA
