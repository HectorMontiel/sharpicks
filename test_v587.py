# -*- coding: utf-8 -*-
"""v587 — la identidad del dueño no se publica: ni en el sitio, ni en el código, ni en los documentos del repositorio.
El SAT sí la conoce; esto es sólo lo que ve el público. Los datos deportivos no cuentan (hay jugadores llamados Héctor)."""
import os
import re
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
IDENTIDAD = re.compile(r'hmrey|h[ée]ctor\s*montiel|hectormontiel|montiel\.ramirez', re.I)
TEXTO = re.compile(r'\.(py|md|ts|sql|yml|yaml|html|js|css|txt|toml|sh|bat|ps1)$')
# el dueño actual del repositorio: se cambia junto con el nombre de la cuenta de GitHub
PERMITIDO = {'modelos_remotos.py': 1, 'precalculo_dia.py': 1, 'publicar_modelos.py': 1, 'test_v587.py': 99}


def _versionados():
    return [f for f in subprocess.check_output(['git', 'ls-files'], cwd=RAIZ).decode('utf-8', 'replace').split('\n') if f]


def test_sin_identidad_en_codigo_ni_documentos():
    malos = {}
    for f in _versionados():
        if not TEXTO.search(f) or not os.path.exists(os.path.join(RAIZ, f)):
            continue
        with open(os.path.join(RAIZ, f), encoding='utf-8', errors='replace') as h:
            n = sum(1 for l in h if IDENTIDAD.search(l))
        if n > PERMITIDO.get(f, 0):
            malos[f] = n
    assert not malos, malos


def test_sitio_sin_identidad():
    for f in _versionados():
        if f.startswith('web/') and TEXTO.search(f):
            with open(os.path.join(RAIZ, f), encoding='utf-8', errors='replace') as h:
                assert not IDENTIDAD.search(h.read()), f


def test_terminos_no_prometen_ni_niegan_factura():
    with open(os.path.join(RAIZ, 'web', 'terminos.html'), encoding='utf-8') as h:
        t = h.read().lower()
    assert 'factura' not in t and 'tax invoice' not in t


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
