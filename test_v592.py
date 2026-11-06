# -*- coding: utf-8 -*-
"""v592 — precios nuevos, el libro de cobros y el paquete fiscal apagado."""
import datetime as dt
import io
import os

import fiscal_mensual as f

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _p(bruto, pagado='2026-12-15T18:00:00+00:00', **k):
    return dict({'bruto': bruto, 'comision': None, 'reembolsado': 0, 'pagado': pagado, 'tipo': 'monedas'}, **k)


def test_tabla_isr_113e():
    assert f.tasa_isr(25000) == .01 and f.tasa_isr(25000.01) == .011 and f.tasa_isr(50000) == .011
    assert f.tasa_isr(83333.33) == .015 and f.tasa_isr(208333.33) == .02 and f.tasa_isr(291666) == .025


def test_calculo_del_mes():
    r = f.resumen([_p(116), _p(232, comision=10.0)], '2026-12')
    assert round(r['cobrado'], 2) == 348 and round(r['base'], 2) == 300 and round(r['iva'], 2) == 48
    assert r['tasa'] == .01 and round(r['isr'], 2) == 3 and r['estimadas'] == 1
    assert r['operaciones'] == 2


def test_reembolso_resta_y_mes_en_hora_de_mexico():
    assert round(f.resumen([_p(116, reembolsado=116)], '2026-12')['cobrado'], 2) == 0
    # 1 de enero a las 03:00 UTC sigue siendo 31 de diciembre en la Ciudad de México
    assert f.mes_de(_p(1, pagado='2027-01-01T03:00:00+00:00')) == '2026-12'


def test_limite_y_pendientes():
    assert f.fecha_limite('2026-12') == '2027-01-17' and f.fecha_limite('2026-11') == '2026-12-17'
    pagos = [_p(1, pagado='2026-11-10T18:00:00+00:00'), _p(1, pagado='2026-12-10T18:00:00+00:00'), _p(1, pagado='2027-01-02T18:00:00+00:00')]
    assert f.meses_pendientes(pagos, dt.date(2027, 1, 5), {'2026-11'}) == ['2026-12']    # ni repite ni manda el mes en curso


def test_documento_sin_datos_de_clientes():
    d = f.documento(f.resumen([_p(116, usuario='uuid-secreto', id='cobro-secreto')], '2026-12'))
    assert 'uuid-secreto' not in d and 'cobro-secreto' not in d and 'Fecha límite' in d and 'Factura global' in d


def test_apagado_por_defecto_y_sin_montos_en_el_registro():
    os.environ.pop('FISCAL_ACTIVO', None)
    assert f.main() == 0
    a = leer('fiscal_mensual.py')
    prints = [l for l in a.splitlines() if 'print(' in l]
    assert all('_d(' not in l and 'texto' not in l for l in prints), prints
    y = leer('.github', 'workflows', 'fiscal_mensual.yml')
    assert 'FISCAL_ACTIVO: ${{ vars.FISCAL_ACTIVO }}' in y and 'fiscal_mensual.py' in y and 'vigia_limites.py' in y


def test_cada_cobro_queda_en_el_libro():
    w = leer('supabase', 'functions', 'stripe-webhook', 'index.ts')
    assert "ev.type === 'invoice.paid'" in w and w.count('anotarPago(') == 3
    assert "'stripe-inv:'" in w and "'stripe:' + s.id" in w
    m = leer('supabase', 'functions', 'mp-webhook', 'index.ts')
    assert m.count('anotarPago(') == 3 and "'mp-rec:'" in m
    s = leer('supabase', 'v592_precios_y_pagos.sql')
    assert 'revoke all on table public.pagos from public, anon, authenticated' in s and 'on delete set null' in s


def test_precios_en_todos_lados():
    s = leer('supabase', 'v592_precios_y_pagos.sql')
    for x in ("set valor = '199' where clave = 'precio_mensual'", "set valor = '149' where clave = 'precio_fundador'", "set valor = '999' where clave = 'precio_semestral'",
              "set valor = '20' where clave = 'lugares_fundador'", "set valor = '15' where clave = 'monedas_bienvenida'", "set precio = 49 where id = 'prueba'", "set precio = 329 where id = 'mega'"):
        assert x in s, x
    h = leer('web', 'index.html')
    assert '$199 <small>al mes</small>' in h and '50 🪙 $49 · 100 🪙 $85 · 220 🪙 $169 · 500 🪙 $329' in h and 'primeros 20' in h and '15 🪙' in h
    for viejo in ('$189', '$129', '$919', 'primeros 50', ' 20 🪙', '>20 🪙'):
        assert viejo not in h, viejo
    c = leer('web', 'cuenta.js')
    assert 'yo.precios.lugares_fundador || 20' in c and "precio_mensual || 199" in c
    for fn in ('vip', 'stripe'):
        t = leer('supabase', 'functions', fn, 'index.ts')
        assert 'A.precio_mensual ?? 199' in t and 'A.precio_fundador ?? 149' in t and 'A.precio_semestral ?? 999' in t


def test_ganamos_mas_por_moneda_y_por_vip():
    limpio = lambda p: p / 1.16 - (.036 * p + 3) * 1.16 - p / 1.16 * .01
    for nuevo, viejo in ((199, 189), (149, 129), (999, 919), (49, 39), (85, 65), (169, 129), (329, 249)):
        assert limpio(nuevo) > limpio(viejo)
    # el paquete grande sigue saliendo más barato por moneda, para premiar comprar más
    por_moneda = [49 / 50, 85 / 100, 169 / 220, 329 / 500]
    assert por_moneda == sorted(por_moneda, reverse=True)


if __name__ == '__main__':
    for n, x in list(globals().items()):
        if n.startswith('test_'):
            x()
            print('ok', n)
