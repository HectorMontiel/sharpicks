# -*- coding: utf-8 -*-
"""v582 — la app en español e inglés. Si alguien agrega un texto visible nuevo sin traducción, aquí truena:
así la app puede crecer sin que un texto se quede en español."""
import io
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(RAIZ, 'web')
ARCH = ['app.js', 'cuenta.js', 'guia.js', 'pistas.js', 'pulso.js', 'fechas.js', 'mudanza.js', 'registro-sw.js']
# código que parece texto, o texto que nunca se ve (consola, errores internos, nombres propios)
NO_SE_VE = re.compile(r'^(\[sharpicks\]|translateX|\(display-mode|\(prefers-reduced|\)uFE0F|" data-|\$1|Bearer$|Escape$|Shar$|English$|Español$|'
                      r'faltan filas|respaldo |respuesta de la base|sin base$|% en$|&nbsp;|\?v=|, \+5)')
PIEZAS = re.compile(r'\b(de|el|la|los|las|en|un|una|con|por|para|del|que|al|y|tu|tus|se|no|sin|hay|ya|lo)\b')


def leer(*p):
    return io.open(os.path.join(*p), encoding='utf-8').read()


def cadenas(js):
    """Las cadenas de un .js, sin comentarios ni expresiones regulares."""
    out, i, n, prev = [], 0, len(js), ''
    while i < n:
        c = js[i]
        if c == '/' and js[i + 1:i + 2] == '/':
            j = js.find('\n', i); i = n if j < 0 else j; continue
        if c == '/' and js[i + 1:i + 2] == '*':
            j = js.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        if c == '/' and prev in '(,=:[!&|?{};\n':
            j, cl = i + 1, False
            while j < n and (js[j] != '/' or cl):
                if js[j] == '\\':
                    j += 1
                elif js[j] == '[':
                    cl = True
                elif js[j] == ']':
                    cl = False
                elif js[j] == '\n':
                    break
                j += 1
            i = j + 1; prev = '/'; continue
        if c in '\'"`':
            j, b = i + 1, []
            while j < n and js[j] != c:
                if js[j] == '\\' and j + 1 < n:
                    b.append({'n': '\n', 't': ' '}.get(js[j + 1], js[j + 1])); j += 2; continue
                if c == '`' and js[j] == '$' and js[j + 1:j + 2] == '{':
                    k, d = j + 2, 1
                    while k < n and d:
                        d += {'{': 1, '}': -1}.get(js[k], 0); k += 1
                    b.append('\x00'); j = k; continue
                b.append(js[j]); j += 1
            out.append(''.join(b)); i = j + 1; prev = 'x'; continue
        if not c.isspace():
            prev = c
        i += 1
    return out


def trozos(s):
    s = re.sub(r'<svg.*?</svg>', ' ', s, flags=re.S)
    attrs = re.findall(r'(?:title|placeholder|aria-label|alt)="([^"]+)"', s)
    t = re.sub(r'<[^>]*>|<[^>]*$|^[^<>]*>', '\x00', s)
    return [x.strip() for x in t.split('\x00')] + attrs


def es_texto(x):
    if len(x) < 2 or not re.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑ]{2}', x):
        return False
    if ' ' in x and not re.search(r'[{}<>]|=>|=[\'"]|https?:', x) and PIEZAS.search(x):
        return True
    if re.fullmatch(r'[a-zA-Z0-9_\-./:#%?&=+,;()\[\]{}*|!\'"\s^$\\]+', x):
        if re.search(r'https?:|^[.#\[]|[{};=]|^\w+[-_]\w+|/', x) or (' ' not in x and x == x.lower()):
            return False
        if re.fullmatch(r'[a-z\-]+( [a-z\-]+)*', x) and not PIEZAS.search(x):
            return False
        if re.fullmatch(r'[A-Z_]{2,}', x) or re.fullmatch(r'[A-Za-z]+[A-Z][a-z]+\w*', x):
            return False
    return not re.search(r'^(function|const|return|var|let) |=>|\.(js|css|png|svg|json)\b|\bdocument\.', x)


def nucleo(s):
    es = lambda c: c == '#' or unicodedata.category(c)[0] in 'LN'
    i, j = 0, len(s)
    while i < j and not es(s[i]):
        i += 1
    while j > i and not es(s[j - 1]):
        j -= 1
    return s[i:j]


def diccionario():
    t = leer(W, 'idioma_en.js')
    return json.loads(t[t.index('{'):t.rindex('}') + 1])


def textos():
    todo = set()
    for a in ARCH:
        for s in cadenas(leer(W, a)):
            todo.update(x for x in trozos(s) if es_texto(x))
    h = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', ' ', leer(W, 'index.html'), flags=re.S)
    todo.update(y for y in (re.sub(r'\s+', ' ', x).strip() for x in trozos(h)) if es_texto(y))
    return todo


def test_todo_texto_visible_tiene_traduccion():
    d = diccionario()
    faltan = []
    for t in textos():
        c = nucleo(t)
        p = re.sub(r'\d+(?:[.,]\d+)?', '#', c)
        if NO_SE_VE.search(t) or not c or c in d or p in d or c[:1].upper() + c[1:] in d:
            continue
        faltan.append(t)
    # v590 — idioma_auto.py traduce lo nuevo al subir a GitHub. Allá, tras traducir, esto sí es estricto (IDIOMA_ESTRICTO).
    if os.environ.get('IDIOMA_ESTRICTO'):
        assert not faltan, 'Sin traducción: ' + repr(sorted(faltan)[:25])
    elif faltan:
        print('se traducirán solos al subir:', len(faltan))
    return faltan


def test_el_extractor_ve_frases_con_punto_y_coma():
    # ya se perdieron textos así: frases sin acentos con «;» parecían código
    assert 'Sirven para abrir un pick premium suelto o una combinada nuestra completa; el precio depende de su cuota.' in textos()


def test_diccionario_coherente():
    d = diccionario()
    assert len(d) > 1000
    for k, v in d.items():
        assert k == nucleo(k), 'llave con puntuación en la orilla (el traductor la quita antes de buscar): ' + k
        assert v, 'sin traducción: ' + k
        assert k.count('#') == v.count('#'), 'los # no cuadran: ' + k
    for k, en in [('Combinada', 'Parlay'), ('Cuota', 'Odds'), ('Roja', 'Loss'), ('Verde', 'Win'), ('Fútbol', 'Soccer'), ('Más de', 'Over')]:
        assert d[k] == en


def test_quien_usa_espanol_no_paga_nada():
    i = leer(W, 'idioma.js')
    assert "if (lang !== 'en') return;" in i
    assert i.index("if (lang !== 'en') return;") < i.index('new MutationObserver')
    assert "if (lang === 'en') document.write('<script src=\"idioma_en.js' + (VER ? '?' + VER : '')" in i   # sólo se baja en inglés, y con versión
    h = leer(W, 'index.html')
    assert 'idioma_en.js' not in h
    assert h.index('idioma.js') < h.index('estilo.css') < h.index('app.js')    # antes que todo lo que pinta


def test_pantalla_banderas_casilla_y_cuenta():
    i = leer(W, 'idioma.js')
    for x in ['Elige tu idioma', 'Choose your language', 'No volver a preguntar', "K_FIJO", 'idioma-btn', '#006847', '#b22234']:
        assert x in i, x
    assert "if (leer(K_FIJO) !== '1') pantalla(true);" in i
    assert 'data-idioma-poner' in leer(W, 'cuenta.js')                       # el cambio desde Mi cuenta
    assert '.idioma-pantalla' in leer(W, 'estilo.css')


def test_fechas_con_el_idioma():
    assert "o.loc || window.I18N.locale" in leer(W, 'app.js')
    c = leer(W, 'cuenta.js')
    assert "Intl.DateTimeFormat('es-MX'" not in c and c.count('Intl.DateTimeFormat(window.I18N.locale') == 3


def test_traductor_en_el_sitio_y_ci():
    y = leer(RAIZ, '.github', 'workflows', 'sitio_web.yml')
    assert 'node --check web/idioma.js' in y and 'node --check web/idioma_en.js' in y


def test_ia_en_los_dos_idiomas():
    import ia_gemini as g
    assert 'analisis_en' in g.ESQUEMA['required'] and 'analisis_en' in g.ESQUEMA_GEN['required']
    v = g.ESQUEMA['properties']['veredictos']['items']
    assert 'motivo_en' in v['required']
    for dep in ['Fútbol', 'NHL', 'Tenis']:
        assert 'analisis_en' in g.instruccion(dep)
    a = leer(W, 'app.js')
    assert "(window.I18N.lang === 'en' && a.analisis_en) || a.analisis" in a
    assert 'add column if not exists analisis_en' in leer(RAIZ, 'supabase', 'v582_ia_analisis_en.sql')
    # lo que queda en español (análisis viejos) no pasa por el traductor: saldría revuelto
    assert 'class="ia-txt" translate="no"' in a


def test_pago_en_su_idioma():
    assert "locale: idioma === 'en' ? 'en' : 'es-419'" in leer(RAIZ, 'supabase', 'functions', 'stripe', 'index.ts')
    assert leer(W, 'cuenta.js').count('idioma: window.I18N.lang') == 2


def test_forma_en_ingles():
    a = leer(W, 'app.js')
    assert a.count("{ G: 'W', E: 'D', P: 'L' }") == 2


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
