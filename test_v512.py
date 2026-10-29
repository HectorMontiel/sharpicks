#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v512 — el sitio se muda a sharpicksapp.com: el dominio viejo lleva a cada usuario CON su sesión (mudanza.js
antes que cuenta.js), el service worker viejo se borra solo, y todo lo que apuntaba al viejo apunta al nuevo.
Sin red."""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
FALLOS = []


def check(cond, msg):
    print(('OK   ' if cond else 'FALLO') + ' ' + msg)
    if not cond:
        FALLOS.append(msg)


def leer(*r):
    with io.open(os.path.join(AQUI, *r), encoding='utf-8') as fh:
        return fh.read()


def probar():
    mw = leer('functions', '_middleware.js')
    check("const VIEJO = 'sharpicks.pages.dev'" in mw and "if (u.hostname !== VIEJO) return ctx.next();" in mw,
          'v512: sólo el dominio viejo exacto se muda (los despliegues de prueba no)')
    check("u.pathname === '/sw.js' || u.pathname === '/mudanza.js'" in mw, 'v512: sw.js y mudanza.js no se redirigen')
    check("Response.redirect(NUEVO + u.pathname + u.search, 301)" in mw, 'v512: lo demás va al mismo camino en el nuevo')
    mu = leer('web', 'mudanza.js')
    check("location.replace(NUEVO + location.pathname + location.search + h)" in mu, 'v512: el viejo lleva al nuevo con la sesión en el #')
    check("document.referrer" in mu and "localStorage.getItem(k) == null" in mu and 'history.replaceState' in mu,
          'v512: en el nuevo sólo se acepta desde el viejo, sin pisar una sesión y borrando el #')
    check("/^(sb-|sp_|sharpicks-)/" in mu, 'v512: sólo se llevan las claves de SharPicks')
    html = leer('web', 'index.html')
    i = html.index('<script src="mudanza.js">')
    check(i < html.index('<script src="config.js">') < html.index('<script src="cuenta.js">'),
          'v512: mudanza.js corre antes de crear el cliente de Supabase')
    sw = leer('web', 'sw.js')
    check("self.registration.unregister()" in sw and "caches.delete" in sw, 'v512: el service worker viejo se borra solo')
    for f in ('exportar_web.py', 'telegram_canales.py', 'avisos_renovacion.py', '.github/workflows/smoke_sharpicks.yml',
              'supabase/functions/entrar/index.ts', 'supabase/functions/monedas/index.ts',
              'supabase/functions/stripe/index.ts', 'supabase/functions/vip/index.ts'):
        s = leer(*f.split('/'))
        check('https://sharpicksapp.com' in s and 'https://sharpicks.pages.dev' not in s, 'v512: %s apunta al dominio nuevo' % f)
    com = leer('supabase', 'functions', 'comentario', 'index.ts')
    check("'https://sharpicksapp.com'," in com and "'https://sharpicks.pages.dev'," in com,
          'v512: los comentarios aceptan los dos dominios mientras dura la mudanza')
    check(not re.search(r'<script>(?!</script>)', html), 'v512: sin scripts en línea (la CSP sigue cerrada)')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
