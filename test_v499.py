#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v499 — el usuario y el código de regalo sin falsos «ya existe» / «no existe»: un error ya no se lee como
«ocupado», el 2.º envío no cuenta, el nombre propio es libre para uno mismo y el código propio vuelve «ok».
Sin red."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*p):
    with open(os.path.join(AQUI, *p), encoding='utf-8') as fh:
        return fh.read()


def probar():
    cu, sql = leer('web', 'cuenta.js'), leer('supabase', 'v499_usuario_y_codigo.sql')
    check("and id is distinct from auth.uid()" in sql, 'v499: el nombre propio cuenta como libre para uno mismo')
    check("if r.usado_por = auth.uid() then return 'ok'; end if;" in sql, 'v499: el código ya canjeado por la misma cuenta vuelve «ok»')
    check("grant execute on function public.usuario_libre(text) to anon, authenticated;" in sql
          and "revoke execute on function public.canjear_codigo(text) from public, anon;" in sql, 'v499: los mismos permisos')
    check('async function usuarioLibre(u)' in cu and "return error ? null : data === true;" in cu,
          'v499: true / false / null (no se pudo comprobar), nunca un error como «ya existe»')
    check(cu.count("sb.rpc('usuario_libre'") == 1 and cu.count('await usuarioLibre(u)') == 3,
          'v499: los tres sitios (crear cuenta, elegir usuario, Mi cuenta) usan la misma comprobación')
    check(cu.count("libre === false ? 'Ese usuario ya existe. Prueba otro.' : NO_SE_PUDO") == 3,
          'v499: «ya existe» sólo cuando de verdad está ocupado')
    check("if (boton && boton.disabled) return;            // v499" in cu and "const listo = ocupado(boton, 'Guardando…');" in cu,
          'v499: elegir usuario bloquea el botón (el 2.º envío ya no cuenta)')
    check("const listo = ocupado(t, 'Canjeando…');" in cu and "data === 'no existe' ? 'Ese código no existe." in cu
          and "esVip() ? '🎉 Ya eres VIP.'" in cu, 'v499: canjear dice lo que de verdad pasó')
    wf = leer('.github', 'workflows', 'sitio_web.yml')
    check('group: sitio-web\n  cancel-in-progress: false' in wf, 'v500: el sitio se publica en cola (antes un disparo nuevo cancelaba al que iba a medias)')
    check("e.code === '23505'" in cu, 'v499: si dos personas eligen el mismo nombre a la vez, la base lo dice')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
