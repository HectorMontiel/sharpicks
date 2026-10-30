"""v539 — el VIP no paga monedas por un pick (desbloquear con es_pro → precio 0)."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def _sql():
    return io.open(os.path.join(RAIZ, 'supabase', 'v539_desbloquear_vip_gratis.sql'), encoding='utf-8').read()


def test_vip_paga_cero():
    s = _sql()
    assert 'es_admin or public.es_pro() then 0' in s


def test_sigue_cobrando_y_sin_anon():
    s = _sql()
    assert 'public.precio_pick(p)' in s
    assert "if p.inicio <= now() then return 'ya empezó'" in s
    assert 'revoke execute on function public.desbloquear(text) from public, anon' in s
