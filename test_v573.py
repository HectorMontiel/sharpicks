"""v573 — las canchas de NHL, NBA, NFL, béisbol y tenis, con la misma lógica que la de fútbol."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


P, A, C = leer('web', 'pistas.js'), leer('web', 'app.js'), leer('web', 'estilo.css')


def test_conectada_sin_tocar_la_de_futbol():
    h = leer('web', 'index.html')
    assert h.index('<script src="pistas.js">') < h.index('<script src="app.js">')
    assert "if (p && p.deporte !== 'Fútbol') return window.Pistas && Pistas.TIENE(p.deporte) ? Pistas.html(v, p, clavePartido(p)) : '';" in A
    assert "pista: window.Pistas && p.deporte !== 'Fútbol' ? Pistas.leer(p.deporte, d, (nos1.team || {}).id) : null," in A
    assert 'function avanzarMotor(k, m, dt)' in A and 'data-motor=' in A       # la de fútbol sigue con su motor
    assert 'https://statsapi.mlb.com' in leer('web', '_headers') and 'node --check web/pistas.js' in leer('.github', 'workflows', 'sitio_web.yml')


def test_cada_deporte_con_su_terreno():
    for clase in ('p-nhl', 'p-nba', 'p-nfl', 'p-beis', 'p-tenis'):
        assert 'class="' + clase + '"' in P and '.' + clase in C
    assert "const ALTO = { NHL: 44.6, NBA: 55.9, NFL: 46.7, BEIS: 84, Tenis: 58 };" in P


def test_la_misma_logica_que_el_futbol():
    assert '.pista-svg[data-pista]:not([data-vivo])' in P and 'n.replaceWith(o);' in P and "o.dataset.firma === n.dataset.firma" in P     # sobrevive al repintado
    assert 'requestAnimationFrame(bucle);' in P and 'const dt = Math.min(0.1, Math.max(0, (ts - tAnt) / 1000));' in P
    assert 'if (sp > tope) { q.vx *= tope / sp; q.vy *= tope / sp; }' in P and 'const d = Math.hypot(dx, dy), tope = 110 * dt;' in P       # nadie salta
    assert 'function lanzar(m, a, conLinea, destino, vel)' in P and 'if (document.hidden) return;' in P and 'if (CALMA) return;' in P


def test_datos_reales_por_deporte():
    assert 'jugadasPista(d, dep, n1)' in P and 'c.x' in P and 'Math.abs(c.x) > 1000' in P                     # los valores basura de la NBA
    assert 'jugadasNfl(d, n1)' in P and 'yardsToEndzone' in P and 'function yardaAx' not in P or 'const yardaAx' in P
    assert "v1.1/game/' + b.pk + '/feed/live'" in P and 'sportId=' in P and 'for (const s of [17, 1])' in P     # incluye ligas de invierno
    assert 'en hockey cambian de lado cada periodo' in P


def test_no_se_inventa_lo_que_cuenta():
    # sólo las jugadas reales disparan gol, canasta o jonrón: el flujo simulado únicamente pasa y conduce
    i, j = P.index('function decidirFlujo(m) {'), P.index('function acomodarNhl(m) {')
    assert 'aviso(' not in P[i:j]
    assert P.count("aviso(m, '¡GOL!'") == 1 and "aviso(m, '¡JONRÓN!'" in P and 'if (real && real.anota)' in P


def test_lo_que_tiene_que_ser_real():
    # el usuario: «si hay alguien en primera, sí está en primera»
    assert "ids: [(of.first || {}).id || null, (of.second || {}).id || null, (of.third || {}).id || null]," in P
    assert 'if (!ant) { q.cx = sitio[0]; q.cy = sitio[1];' in P and 'const j = ant.indexOf(id), o = j >= 0 ? BASES[j] : HOME;' in P
    assert "classList.toggle('ocupada', !!b['en' + el.dataset.base])" in P and "el.classList.add('nombrado')" in P
    # los que están en juego y quien hace cada jugada
    assert 'function enHielo(d, n1)' in P and 'function enCancha(js, pl)' in P and 'real = id && m.js.find((j) => j.id === id);' in P
    # la línea de golpeo y el primer intento salen de la jugada real
    assert 'm.losX = yardaAx(entre(0, u.ydF, 100), m.of);' in P and 'Number(u.dist) * 0.875' in P


def test_el_reloj_de_cada_liga():
    # medido: la NHL cuenta lo jugado (0:33, 5:55…) y la NBA lo que falta (12:00, 6:26…)
    assert "(dep === 'NHL' ? Math.min(largo, clk) : Math.max(0, largo - clk))" in P


def test_todo_en_espanol():
    for t in ('Saque de centro', 'Tiro a puerta', 'Pérdida', 'Tiempo muerto', 'Pase completo', 'Captura', 'Jonrón', 'Ponche', 'Gol de campo fallado'):
        assert t in P
    assert 'function etiqueta(fam, q, nombres)' in P and 'anunciar(m, etiqueta(m.fam, nueva, m.datos.nombres));' in P
    assert 'const bajaEs = ' in P


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
