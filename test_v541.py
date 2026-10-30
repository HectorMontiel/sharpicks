"""v541-v543 — la app cabe en cualquier iPhone/iPad, precios con IVA y comisión, el vigilante de límites y la huella."""
import datetime as dt
import io
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_cabe_en_iphone_y_ipad():
    css = leer('web', 'estilo.css')
    assert '@media (pointer: coarse) { input, select, textarea { font-size: 16px !important; } }' in css   # sin zoom en iPhone
    assert '@media (min-width: 900px) { .nav-abajo { left: 50%; right: auto; width: 640px;' in css         # iPad horizontal
    assert '.cuenta .entrar { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }' in css


def test_precios_con_iva():
    s, html = leer('supabase', 'v541_precios_iva.sql'), leer('web', 'index.html')
    assert "set valor = '189' where clave = 'precio_mensual'" in s and "set precio = 39 where id = 'prueba'" in s
    assert '$189 <small>al mes</small>' in html and '50 🪙 $39 · 100 🪙 $65 · 220 🪙 $129 · 500 🪙 $249' in html
    # cada precio deja limpio, tras IVA y comisión de Stripe, al menos el precio de antes
    limpio = lambda p: p / 1.16 - (0.036 * p + 3) * 1.16
    for nuevo, viejo in ((189, 149), (129, 99), (919, 749), (39, 29), (65, 49), (129, 99), (249, 199)):
        assert limpio(nuevo) >= viejo - 1, (nuevo, viejo, limpio(nuevo))


def test_vigilante_avisa_al_80_y_95():
    import vigia_limites as v
    hoy = dt.date(2026, 11, 10)
    f = {'base_mb': 100, 'mau': 41000, 'altas_dia': 10}
    av = v.evaluar(f, {'egreso': 2.0 * v.GB, 'funciones': 1000}, 10, hoy)
    met = {m: n for m, n, _, _, _ in av}
    assert met.get('mau') == 80                      # 41 000 de 50 000 = 82 %
    assert met.get('egreso_mes') == 95               # 2 GB en 10 días → 6 GB al cierre = 120 % proyectado
    assert 'base_mb' not in met and 'funciones_mes' not in met
    assert all('Qué hacer:' in t for *_, t in av)


def test_vigilante_en_la_nube():
    wf = leer('.github', 'workflows', 'vigia_limites.yml')
    assert 'runs-on: ubuntu-latest' in wf and 'python3 vigia_limites.py' in wf and 'SUPABASE_ACCESS_TOKEN' in wf
    s = leer('supabase', 'v542_vigia_limites.sql')
    assert 'revoke all on public.vigia_uso from public, anon, authenticated;' in s


def test_huella_evita_bajar_todo():
    a, c, s = leer('web', 'app.js'), leer('web', 'cuenta.js'), leer('supabase', 'v543_huella_publica.sql')
    assert "h.picks === _huella.picks" in a and "/rest/v1/rpc/huella_publica" in a
    assert "setInterval(() => { if (!document.hidden) cargar(); }, 3 * 60 * 1000);" in a
    assert 'Date.now() - yo._pesadoEn > 10 * 60e3' in c
    assert 'grant execute on function public.huella_publica(date, date) to anon, authenticated;' in s
