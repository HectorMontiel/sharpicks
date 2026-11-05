"""v570 — la cancha de fútbol sin brincos: motor continuo y lista que no redibuja lo que no cambió."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


APP, CSS = leer('web', 'app.js'), leer('web', 'estilo.css')


def test_la_cancha_sobrevive_al_repintado():
    # el brinco del video: cada repintado creaba la cancha y los 22 saltaban a su destino
    assert ".cancha-svg[data-motor]:not([data-vivo])" in APP and 'n.replaceWith(o);' in APP and 'o.dataset.firma === n.dataset.firma' in APP
    assert 'data-firma="' in APP and "const yaCorre = !!m.js;" in APP and 'if (u && !pausa && !yaCorre) {' in APP
    # tiros y letrero sí se actualizan en la que sigue viva
    assert "o.querySelectorAll('.tiro, .letrero').forEach((x) => x.remove());" in APP


def test_movimiento_continuo_con_tope_de_velocidad():
    assert 'requestAnimationFrame(moverCanchas);' in APP and 'setInterval(moverCanchas' not in APP
    assert 'const dt = Math.min(0.1, Math.max(0, (ts - _tCancha) / 1000));' in APP          # tras un trabón sigue donde iba
    assert 'if (sp > tope) { q.vx *= tope / sp; q.vy *= tope / sp; }' in APP                 # nadie puede saltar
    assert '.cancha-svg .jug, .cancha-svg .balon { transition: none;' in CSS and 'transition: transform 1s linear' not in CSS


def test_el_balon_vuela_y_el_dueno_cambia_al_llegar():
    assert 'function lanzar(m, a, conLinea)' in APP and 'm.port = null; m.portador = null;' in APP
    assert 'm.port = v.a; m.portador = v.a.key; m.vuelo = null;' in APP


def test_mas_accion_y_nadie_amontonado():
    assert '? 48 : 28' in APP and 'm.carrera' in APP and 'nadie encima de nadie' in APP and 'nadie se queda parado' in APP


def test_lo_que_se_anima_no_inventa_tiros_ni_goles():
    # tiros, goles y tarjetas sólo salen de una jugada real o de lo que suben las estadísticas
    i, j = APP.index('function decidir(k, m) {'), APP.index('// el lugar al que va cada uno')
    assert "m.escena" not in APP[i:j] and "'goal'" not in APP[i:j] and 'shot' not in APP[i:j]


def test_se_distinguen_equipos_y_marcas():
    assert 'const chocan = (a, b) =>' in APP and 'if (chocan(a, b)) {' in APP and 'const verdoso = (h) =>' in APP and 'const enPasto = (x, otro) =>' in APP
    assert '<span>× tiro</span><span>★ gol</span>' in APP and 'class="bal"' not in APP


def test_sin_trabarse_solo_cambia_lo_que_cambio():
    assert "ponerLista($('tarjetas')," in APP and 'function mezclarLista(a, b, nivel)' in APP and 'if (x.isEqualNode(y)) return;' in APP
    assert "$('tarjetas').innerHTML = (estado.vista" not in APP


def test_quien_pide_menos_movimiento():
    assert "prefers-reduced-motion: reduce)').matches" in APP and 'if (CALMA) return;' in APP


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
