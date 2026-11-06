"""v577 — tenis con su marcador real y peloteo continuo; marcador propio en cada cancha; la presión ya no sale plana."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


P, A, C, V = leer('web', 'pistas.js'), leer('web', 'app.js'), leer('web', 'estilo.css'), leer('functions', 'vivo.js')


def test_el_tenis_sigue_hasta_el_punto_real():
    assert 'function queCambio(a, b)' in P and 'function marcadorTenis(m)' in P and "aviso: '¡PUNTO!'" in P and "aviso: '¡JUEGO!'" in P and "aviso: '¡SET!'" in P
    # el marcador se enseña al terminar el punto en la cancha, no antes
    assert 'm.tenis = m.tenU;' in P and 'if (c && !m.punto) m.punto = c;' in P
    # gana quien de verdad ganó
    assert 'if (g == null || g === a.lado) {' in P
    # ya no se va la bola a un lado de la cancha a esperar
    assert 'm.bt = [52.5, 55]' not in P


def test_el_marcador_del_tenis_nunca_retrocede():
    assert 'avanceT(ahora) >= avanceT(m.tenU)' in P and 'const avanceT = (x) =>' in P


def test_el_vivo_trae_sets_puntos_y_saque():
    assert 'function extraTenis(c)' in V and "['BA', 'BB']" in V and 'c.WA != null' in V and "c.WC === '1' ? 0 : c.WC === '2' ? 1 : null" in V
    assert "dep === DEPORTES.tenis" in V and "'Cache-Control': 'public, max-age=30'" in V


def test_cada_cancha_con_su_marcador():
    for clase in ('mc-nba', 'mc-nhl', 'mc-nfl', 'mc-beis', 'mc-tenis'):
        assert "'" + clase + "'" in P and '.' + clase in C
    assert 'mc-fut' in A and '.mc-fut' in C
    assert 'function tablero(d, n1)' in P and 'marc: tablero(d, n1)' in P and 'function diamante(' not in P and 'const diamante = (b)' in P
    assert "svg.parentElement.querySelector('.mc-caja')" in P and 'o._mc = null;' in P


def test_la_presion_no_es_plana():
    assert 'function curvaPresion(k, tramos, ahora, fin, goles)' in A and 'barra(xm(a) + 0.4' not in A
    assert 'else while (ya.length < n) ya.push(hasta);' in A                          # lo que llega en vivo, en su minuto
    assert 'Presión <small class="tenue">aprox.</small>' in A                         # dice que es aproximada
    assert 'Presión estimada con las acciones reales de cada tiempo' in A


def test_el_ritmo_es_el_del_partido():
    # el usuario: «cambian las jugadas muy drásticamente». ESPN las entrega en grupo; se respetan los segundos reales entre una y otra
    assert '(nueva.min - antes.min) * 60' in P and 'if (m.t >= m.listo) {' in P
    assert "if (/Substitution/.test(t)) return [];" in P and 'm.suelta = m.t + 3.5' in P
    assert "(port.cx - 52.5) * port.dir < 4" in P                                     # el base sube botando
    assert 'const llega = tiene ?' in P


def test_el_marcador_no_se_adelanta_a_la_jugada():
    assert 'const hayPend = m && m.ultReal && m.ultReal.g' in P and 'const g = hayPend ? m.ultReal.g : v.g' in P


def test_nfl_sin_jugadas_inventadas():
    i, j = P.index('function nfl(m) {'), P.index('// ------------- béisbol: lanzamiento a lanzamiento')
    assert 'nflJugada(m, null)' not in P and 'nflJugada(m, nueva)' in P[i:j]
    assert 'function nflHuddle(m)' in P and 'function nflMovimiento(m)' in P
    # la yarda final, con el equipo que se queda el balón: en despejes e intercepciones cambia
    assert 'real.equipoFin == null ? L : real.equipoFin' in P and 'm.jugadaNfl || (m.datos' in P


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
