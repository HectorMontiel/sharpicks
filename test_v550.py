"""v550 — las patas de las combinadas del usuario (y lo seguido y desbloqueado) no se borran; una pata que ya no existe
se ve como «retirada» y no cuenta; si faltó alguna, el premio va con la cuota armada."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_no_se_borra_lo_que_usan_los_usuarios():
    ex = leer('exportar_web.py')
    assert "base + 'combinadas_usuario'" in ex and "base + 'seguidos'" in ex and "base + 'desbloqueos'" in ex
    assert "out |= set(c.get('patas') or [])" in ex and "base + 'telegram_enviados'" in ex


def test_liquidacion_con_patas_retiradas():
    s = leer('supabase', 'v550_combinadas_patas_retiradas.sql')
    assert "if v_hay < cardinality(c.patas) then v_cuota := c.cuota; end if;" in s
    assert "continue;                                   -- aún se juega lo que queda: espera" in s


def test_la_pagina_lo_dice():
    c = leer('web', 'cuenta.js')
    assert "Pick retirado por el modelo antes del partido · no cuenta" in c
    assert "Ya cobraste la premiada de ese día" in c


def test_v551_pata_del_armador_abre_el_partido():
    a = leer('web', 'app.js')
    assert "'<button type=\"button\" class=\"arm-pata' + (ia ? ' ia-' + ia : '') + '\" data-ficha=\"' + esc(p.id) + '\"" in a
