# -*- coding: utf-8 -*-
"""v593 — tarjeta más corta y acceso directo al Pulso."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_pulso_abre_directo():
    a = leer('web', 'app.js')
    f = a[a.index('function pulsoChip'):a.index('function candidatosPulso')]
    assert 'data-ficha-ir="pulso"' in f and f.count('<button type="button" class="pulso-chip') == 2
    assert "t.dataset.fichaIr === 'pulso'" in a and "querySelector('.pulso')" in a
    assert 'pulsoChip(p, v, (ps.find((x) => x.espn) || p).id)' in a


def test_patas_en_un_renglon_sin_quitar_nada():
    a = leer('web', 'app.js')
    f = a[a.index('const extra = window.SPX ? SPX.extra(p)'):a.index('// ---------- v396: COMBINADAS')]
    assert '<details class="pick-fila compacta pk-det' in f and '<summary class="pk-top">' in f
    for x in ('pk-cuota', 'estadoPick(p, v)', 'pct(p.prob)', 'grado(p)', 'extra +', 'iaDelPick(p)', 'p.porque'):
        assert x in f, x
    assert f.index('</summary>') < f.index('pct(p.prob)')
    assert f.index('estadoPick(p, v)') < f.index('</summary>')   # verde o roja a la vista


def test_desbloquear_nunca_queda_escondido():
    a = leer('web', 'app.js')
    assert """(/class="desbloquear"/.test(extra) ? ' open' : '')""" in a
    assert 'class="desbloquear"' in leer('web', 'cuenta.js')


def test_seccion_se_oculta_y_sigue_oculta():
    a = leer('web', 'app.js')
    assert '<details class="ctx picks-sec" open><summary>' in a and 'Apuestas del modelo' in a
    assert 'const picksCerrados = new Set()' in a
    r = a[a.index('function restaurarVista'):]
    assert r.index('picksCerrados') < r.index('if (!m) return;')
    assert '.pick-fila.pk-det' in leer('web', 'estilo.css')


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
