"""v540 — cabecera sin encimarse, guía con Atrás y recompensas, armador por días/deportes/partidos, gratis con
cualquier nivel pagando monedas, VIP con el morado primero, y el mismo partido con dos nombres unido."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_cabecera_no_se_encima():
    css = leer('web', 'estilo.css')
    assert '.marca { flex: 1 1 0; min-width: 40px; overflow: hidden; container-type: inline-size; }' in css
    assert '@container (max-width: 108px) { .marca #nombre { display: none; } }' in css


def test_guia_atras_y_recompensas():
    g = leer('web', 'guia.js')
    assert 'class="guia-atras">Atrás</button>' in g and 'paso(i - 1, -1)' in g
    assert "t: '🪙 Tu combinada paga'" in g
    assert "window.addEventListener('scroll', colocar, { passive: true });" in g


def test_armador_dias_deportes_partidos():
    a = leer('web', 'app.js')
    assert "const ARM_DIAS = [['hoy', 'Hoy'], ['manana', 'Mañana'], ['pasado', 'Pasado']];" in a
    assert 'data-arm-dia=' in a and 'data-arm-dep=' in a and 'data-arm-par=' in a
    assert 'Los que marques entran sí o sí' in a


def test_gratis_paga_y_vip_morado_primero():
    a, c = leer('web', 'app.js'), leer('web', 'cuenta.js')
    assert 'Plan gratis: 🥇 Oro y los 🎁 gratis del día sin costo. Puedes meter otros niveles; esas patas cuestan 🪙 según su cuota.' in a
    assert 'const orden = (a, b) => (iaSegura(b) - iaSegura(a)) || (Number(b.prob) - Number(a.prob));' in a
    assert "sb.rpc('desbloquear_varios', { p_ids: ids.slice(0, 20) })" in c
    s = leer('supabase', 'v540_desbloquear_varios.sql')
    assert "if coalesce(saldo, 0) < total then return 'sin monedas'; end if;" in s
    assert 'r := public.desbloquear(v_id);' in s and 'revoke all on function public.desbloquear_varios(text[]) from public, anon;' in s


def test_mismo_partido_dos_nombres():
    a = leer('web', 'app.js')
    assert "const clavePartido = (p) => (p && typeof p === 'object' && canonicas().get(p)) || claveNombre(p);" in a
    assert "let k = p.espn ? porEspn.get(p.deporte + '|' + p.espn) : null;" in a
