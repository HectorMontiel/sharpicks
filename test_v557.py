"""v557 — en el armador, ↻ cambia sólo esa pata por la siguiente más probable; las demás no se mueven. Si ya no hay de
los niveles elegidos, sigue con otros niveles; si no hay ninguna, la pata se queda y se avisa."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def cuerpo_cambiar():
    a = leer('web', 'app.js')
    return a[a.index('function cambiarPata(id)'):a.index('function pintarArmador()')]


def test_solo_cambia_esa_pata():
    c = cuerpo_cambiar()
    assert 'r.patas[i] = { p: nueva, v: veredictoIA(nueva) };' in c
    assert 'j !== i' in c and '!quedan.has(clavePartido(p))' in c


def test_orden_de_la_siguiente():
    c = cuerpo_cambiar()
    assert 'if (misma && marcado) return 0;' in c
    assert "(sel.has(nivel(p).n) || libre ? 1 : 3) + (misma ? 1 : 0)" in c
    assert '(tanda(a) - tanda(b)) || (iaSegura(b) - iaSegura(a)) || (Number(b.prob) - Number(a.prob))' in c


def test_respeta_lo_que_ya_filtraba_el_armador():
    c = cuerpo_cambiar()
    assert "veredictoIA(p) !== 'contra'" in c and '(!A.soloIA || iaSegura(p))' in c and 'armBase()' in c


def test_sin_otra_se_queda_y_avisa():
    a = leer('web', 'app.js')
    c = cuerpo_cambiar()
    assert c.index('if (!nueva) return;') < c.index('A.quitadas.add(id);')
    assert "r.sinMas ? '<p class=\"aviso\">Ya no hay otra pata" in a


def test_lo_quitado_no_regresa_y_se_puede_devolver():
    a = leer('web', 'app.js')
    assert 'base = armBase().filter((p) => !A.quitadas.has(p.id));' in a
    assert 'if (t.dataset.armRestaurar) { estado.arm.quitadas.clear(); estado.arm.res = armarCombinada();' in a


def test_el_boton_va_fuera_de_la_pata():
    a = leer('web', 'app.js')
    # un botón dentro de otro no es válido: ↻ va al lado, en la misma fila
    assert '\'<span class="arm-ir">›</span></button>\' +' in a
    assert 'class="arm-cambiar" data-arm-cambiar="' in a
    assert '[data-arm-cambiar],[data-arm-restaurar]' in a
    assert '.arm-pata-fila {' in leer('web', 'estilo.css')
