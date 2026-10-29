#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v506 — donde la casa cotiza, «se mete» sólo hasta cuota 1,23 (medido: entre las «se mete» la cuota separa
verdes de rojas y nuestra probabilidad no). Los dos casos del usuario. Sin red."""
import veredicto_pick as vp

FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def v(apuesta, mercado, prob, pm, cuota):
    return {'veredicto': vp.METER, 'mercado': mercado, 'apuesta': apuesta, 'prob_ajustada': prob,
            'p_mercado': pm, 'cuota': cuota, 'pick': {'deporte': 'Fútbol', 'mercado': mercado}}


def probar():
    check(vp.METER_CASA_CUOTA_MAX == 1.23 and vp.CUOTA_METER_FUTBOL_MAX == 1.35,
          'v506: tope 1,23 con precio de la casa; 1,35 sigue para lo que no tiene precio')
    bayern = vp.franja_futbol(v('Goles: Menos de 6.5', 'Goles', 0.8073, 0.80, 1.231))
    check(bayern is not None and '1.23' in bayern, 'v506: Bayern–Magdeburg «Menos de 6.5» a 1,231 ya no se mete')
    portland = vp.franja_futbol(v('Goles Portland Timbers: Menos de 2.5', 'Goles equipo', 0.8611, 0.84, 1.154))
    check(portland is None, 'v506: «Goles Portland: Menos de 2.5» a 1,154 sigue (familia que acierta 86-90 % a esa cuota)')
    check(vp.franja_futbol(v('Goles: Más de 1.5', 'Goles', 0.80, 0.80, 1.23)) is None, 'v506: 1,23 justo entra')
    check(vp.franja_futbol(v('Goles: Más de 1.5', 'Goles', 0.80, 0.80, 1.30)) is not None, 'v506: 1,30 ya no')
    # sin precio (córners) no cambia: sigue el tope 1,35
    sin = {'veredicto': vp.METER, 'mercado': 'Córners', 'apuesta': 'Córners X: Más de 3.5', 'prob_ajustada': 0.75,
           'cuota': 1.30, 'pick': {'deporte': 'Fútbol', 'mercado': 'Córners'}}
    check(vp.franja_futbol(sin) is None, 'v506: córners a 1,30 (sin precio de la casa) siguen igual')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
