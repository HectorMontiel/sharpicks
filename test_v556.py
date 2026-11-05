"""v556 — la pata de una combinada, antes de empezar, abre la tarjeta completa (estadísticas previas y análisis
con IA), no la ficha chica. Ya empezado el partido, sigue abriendo la ficha con marcador y cancha."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_las_tres_patas_van_a_la_tarjeta():
    a = leer('web', 'app.js')
    assert "if (t.matches('.arm-pata,.comb-pata,.tg-pata')) abrirPata(t.dataset.ficha); else ficha(t.dataset.ficha);" in a
    # las tres listas siguen marcando sus patas con data-ficha
    assert 'class="arm-pata' in a and 'class="comb-pata"' in a
    assert 'class="tg-pata ir-partido" data-ficha=' in leer('web', 'cuenta.js')


def test_solo_antes_de_empezar():
    a = leer('web', 'app.js')
    assert "if (faseDe(ps) !== 'proximo') { ficha(id); return; }" in a
    assert "tarjeta(ps, true)" in a
    # la tarjeta trae lo previo y la IA, y no vuelve a mandar a la ficha chica
    cuerpo = a[a.index('function tarjeta(ps, previa)'):a.index('// v513 — en la tarjeta en vivo')]
    assert 'contextoHtml(' in cuerpo and 'iaBloque(' in cuerpo
    assert "(!previa && ps.some((x) => x.espn) ? '<button class=\"ver\"" in cuerpo


def test_al_repintar_no_se_pierde_lo_abierto():
    a = leer('web', 'app.js')
    assert "pintar: () => { pintar(); if (fichaPrevia) refrescarFicha(); }" in a
    assert "if (fichaPrevia) abrirPata(fichaId); else ficha(fichaId);" in a
    assert "c.querySelectorAll('details').forEach((d, i) => { if (abiertas[i]) d.open = true; });" in a
    # la ficha normal no se queda con el modo de la tarjeta
    assert "fichaId = id; fichaPrevia = false;" in a


def test_el_candado_vip_no_deja_la_tarjeta_encima():
    assert "if (t.closest('#ficha')) { $('ficha').hidden = true; fichaId = null; }" in leer('web', 'app.js')


def test_sin_marco_doble():
    assert '.ficha-caja.previa {' in leer('web', 'estilo.css')


if __name__ == '__main__':
    # la suite corre cada prueba como script: sin esto, estas funciones no se ejecutan y siempre sale «sin fallos»
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
