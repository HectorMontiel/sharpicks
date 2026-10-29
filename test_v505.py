#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v505 — un pick con y sin 🏆 es el MISMO pick (mismo id): antes quedaban los dos («Plata y Platino tienen
el mismo pick»). Sin red."""
import exportar_web as ew

FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def probar():
    a = {'fecha': '2026-10-28', 'partido': 'Inter Miami vs FC Cincinnati', 'apuesta': 'Inter Miami o empate'}
    con = dict(a, apuesta='🏆 Inter Miami o empate')
    check(ew._id(a) == 'efee48203740b34a3502', 'v505: el id sin marca no cambia (el publicado)')
    check(ew._id(con) == ew._id(a), 'v505: con 🏆 es el mismo id')
    check(ew._id(dict(a, apuesta='⭐ 🏆 Inter Miami o empate')) == ew._id(a), 'v505: con ⭐ y 🏆 también')
    check(ew._id(dict(a, apuesta='Gana Inter Miami')) != ew._id(a), 'v505: otra apuesta, otro id')
    f1, f2 = ew._fila(a, 'pendiente'), ew._fila(dict(con, prob=0.85), 'vivo')
    check(f1['id'] == f2['id'] and f1['apuesta'] == f2['apuesta'], 'v505: las dos filas se juntan en una')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
