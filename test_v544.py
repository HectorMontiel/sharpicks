"""v545-v547 — los niveles nuevos (🥇 Oro = 70-79 % y cuota ≥ 1,25) y ya sin picks de regalo (v547)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _p(i, fecha, prob, elige=False, cuota=1.2):
    return {'id': 'p%d' % i, 'fecha': fecha, 'prob': prob, 'elige': elige, 'cuota': cuota, 'estado': 'pendiente', 'tipo': 'pick'}


def test_niveles_v545():
    import exportar_web as ew
    import telegram_canales as tc
    for f in (ew.nivel, tc.nivel):
        assert f(_p(1, 'd', 0.86, elige=True)) == 'Diamante'
        assert f(_p(1, 'd', 0.82)) == 'Platino'                  # antes Oro: ahora 80 %+ es Platino
        assert f(_p(1, 'd', 0.72, cuota=1.30)) == 'Oro'          # más cuota, menos probabilidad
        assert f(_p(1, 'd', 0.79, cuota=1.20)) == 'Plata'        # 79 % con cuota baja
        assert f(_p(1, 'd', 0.66, cuota=1.60)) == 'Plata'


def test_sin_regalos():
    import exportar_web as ew
    assert not hasattr(ew, 'gratis_del_dia') and not hasattr(ew, 'GRATIS_DIA')   # v547 — el usuario: «quita los picks de regalo»


if __name__ == '__main__':
    test_niveles_v545()
    test_sin_regalos()
    print('TODO OK')
