"""v544-v545 — cada día el gratis tiene al menos 2 picks sin costo: el 🥇 Oro (70-79 % y cuota ≥ 1,25) y, si no alcanza,
regalos con más cuota y menos probabilidad (Plata 65 %+ con la cuota más alta; si no hay, el Platino menos probable).
El 💎 Diamante nunca se regala; lo ya regalado se queda gratis."""
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


def test_gratis_del_dia():
    os.environ['PREMIUM_NIVELES'] = 'Diamante,Platino,Plata,Cuota alta'
    import exportar_web as ew
    ps = [_p(1, 'd1', 0.86, elige=True), _p(2, 'd1', 0.79, cuota=1.20), _p(3, 'd1', 0.68, cuota=1.45), _p(4, 'd1', 0.85),
          _p(5, 'd1', 0.50, cuota=2.5)]
    n = ew.gratis_del_dia(ps)
    g = {p['id'] for p in ps if p.get('gratis')}
    assert g == {'p3', 'p2'} and n == 2                    # Plata de 65 %+, la de más cuota primero; ni Platino ni Diamante
    ps = [_p(1, 'd1', 0.72, cuota=1.30), _p(2, 'd1', 0.79, cuota=1.20), _p(3, 'd1', 0.90)]
    ew.gratis_del_dia(ps)
    assert [p['id'] for p in ps if p.get('gratis')] == ['p2']   # ya hay 1 Oro: sólo falta un regalo
    ps2 = [_p(1, 'd1', 0.79), _p(2, 'd1', 0.79), _p(3, 'd1', 0.79), _p(4, 'd1', 0.79)]
    ew.gratis_del_dia(ps2, antes={'p4'})
    assert ps2[3].get('gratis')                             # lo que ya salió gratis se queda gratis
    os.environ.pop('PREMIUM_NIVELES', None)
    assert ew.gratis_del_dia([_p(1, 'd1', 0.79)]) == 0      # sin modo de pago no hace nada


if __name__ == '__main__':
    test_niveles_v545()
    test_gratis_del_dia()
    print('TODO OK')
