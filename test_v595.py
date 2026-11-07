#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v595 — todas las cuotas son aproximadas y al usuario no se le nombra ninguna casa."""
import re

_fallos = []


def ok(nombre, cond):
    print(('OK   ' if cond else 'FALLA') + ' ' + nombre)
    if not cond:
        _fallos.append(nombre)


def lee(p):
    return open(p, encoding='utf-8').read()


CASAS = re.compile(r'playdoit|pinnacle|novibet|caliente|bovada|draftea|1xbet|winpot|sportium|unibet|matchbook|draftkings', re.I)


def sin_comentarios_js(t):
    return re.sub(r'(^|\s)//[^\n]*', ' ', re.sub(r'/\*.*?\*/', ' ', t, flags=re.S))


for ruta in ('web/app.js', 'web/cuenta.js', 'web/index.html', 'web/terminos.html', 'web/privacidad.html', 'web/idioma_en.js'):
    t = lee(ruta)
    t = sin_comentarios_js(t) if ruta.endswith('.js') else t
    ok('%s sin nombres de casas' % ruta, not CASAS.search(t))

app, cuenta = lee('web/app.js'), lee('web/cuenta.js')
for nombre, t in (('app', app), ('cuenta', cuenta)):
    # Toda cuota que se pinta lleva la tilde delante
    sueltas = re.findall(r"(?<!~' \+ )(?:Number\((?:p|x|c)\.cuota(?: \|\| 0)?\)|\bcuota)\.toFixed\(2\)", t)
    ok('%s: ninguna cuota sin «~»' % nombre, not sueltas)
    ok('%s: sin doble tilde' % nombre, "~<b>' + '~'" not in t and "~' + '~'" not in t)
ok('la página dice que son aproximadas', 'aproximadas' in lee('web/index.html'))
ok('los términos dicen que son aproximadas', 'aproximadas' in lee('web/terminos.html'))

err = lee('errores_web.py')
ok('errores: sin casa en lo que se publica', "'casa': None" in err and '(Pinnacle) en' not in err)
tg = lee('telegram_canales.py')
ok('Telegram: la cuota con «~»', "💸 ~%.2f" in tg and "💸 %.2f" not in tg)
ok('Telegram: sin casa', "p.get('casa')" not in tg)
tj = lee('tarjeta_tg.py')
ok('imagen de Telegram: cuotas con «~»', not re.search(r"'%\.2f' % cuota", tj))

print('\n%d fallos' % len(_fallos))
raise SystemExit(1 if _fallos else 0)
