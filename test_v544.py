"""v544 — cada día el gratis tiene al menos 3 picks sin costo (Oro, o los mejores de Plata/Platino); Diamante nunca."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _p(i, fecha, prob, elige=False, cuota=1.2):
    return {'id': 'p%d' % i, 'fecha': fecha, 'prob': prob, 'elige': elige, 'cuota': cuota, 'estado': 'pendiente', 'tipo': 'pick'}


def test_gratis_del_dia(monkeypatch=None):
    os.environ['PREMIUM_NIVELES'] = 'Diamante,Platino,Plata,Cuota alta'
    import exportar_web as ew
    ps = [_p(1, 'd1', 0.86, elige=True), _p(2, 'd1', 0.79, cuota=1.3), _p(3, 'd1', 0.79, cuota=1.1), _p(4, 'd1', 0.85),
          _p(5, 'd1', 0.70), _p(6, 'd2', 0.82), _p(7, 'd2', 0.81), _p(8, 'd2', 0.83), _p(9, 'd2', 0.79)]
    n = ew.gratis_del_dia(ps)
    g = {p['id'] for p in ps if p.get('gratis')}
    assert g == {'p4', 'p3', 'p2'} and n == 3                 # d1: Platino y las dos Plata (la de cuota más baja antes)
    assert 'p1' not in g                                    # el Diamante nunca se regala
    ps2 = [_p(1, 'd1', 0.79), _p(2, 'd1', 0.79), _p(3, 'd1', 0.79), _p(4, 'd1', 0.79)]
    ew.gratis_del_dia(ps2, antes={'p4'})
    assert ps2[3].get('gratis')                             # lo que ya salió gratis se queda gratis
    os.environ.pop('PREMIUM_NIVELES', None)
    assert ew.gratis_del_dia([_p(1, 'd1', 0.79)]) == 0      # sin modo de pago no hace nada


if __name__ == '__main__':
    test_gratis_del_dia()
    print('TODO OK')
