# -*- coding: utf-8 -*-
"""v590 — sin sellos que prometan acierto no medido, y el inglés se escribe solo."""
import io
import json
import os

import idioma_auto as ia

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def test_sin_promesa_de_acierto_en_morado():
    for f in ('app.js', 'guia.js', 'cuenta.js', 'idioma_en.js'):
        t = leer('web', f)
        for x in ('IA_SALIO', 'salió 91', 'aciertan 91', '91 % medido', 'Modelo + IA', 'Model + AI'):
            assert x not in t, (f, x)


def test_llave_y_validacion():
    assert ia.llave('✨ Faltan 12 días.') == 'Faltan # días'
    assert ia.valida('Faltan # días', '# days left')
    assert not ia.valida('Faltan # días', 'Days left')           # se perdió el número
    assert not ia.valida('Hola', '   ') and not ia.valida('Hola', None)


def test_agregar_no_pisa_lo_existente():
    js = 'window.I18N_EN = {\n"Hola": "Hello",\n"Adiós": "Bye"\n};\n'
    n = ia.agrega(js, {'Hola': 'OTRA', 'Nuevo': 'New.'})
    d = json.loads(n[n.index('{'):n.rindex('}') + 1])
    assert d == {'Hola': 'Hello', 'Adiós': 'Bye', 'Nuevo': 'New'}
    assert n.endswith('};\n')
    assert ia.agrega(js, {'Hola': 'OTRA'}) == js


def test_flujo_solo_toca_el_diccionario():
    y = leer('.github', 'workflows', 'idioma_auto.yml')
    assert 'git add web/idioma_en.js' in y and "'!web/idioma_en.js'" in y and 'IDIOMA_ESTRICTO' in y
    assert 'gh workflow run web_rapido.yml' in y and 'node --check web/idioma_en.js' in y


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
