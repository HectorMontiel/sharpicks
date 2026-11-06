# -*- coding: utf-8 -*-
"""v584 — los picks de pago no vuelven a quedar en claro en el repositorio público."""
import io
import json
import os
import shutil
import subprocess
import tempfile

import cajon

RAIZ = os.path.dirname(os.path.abspath(__file__))


def leer(*p):
    return io.open(os.path.join(RAIZ, *p), encoding='utf-8').read()


def _dir():
    d = tempfile.mkdtemp(prefix='v584_')
    return d


def test_ida_y_vuelta():
    d = _dir()
    try:
        original = json.dumps({'apuesta': 'Goles: Menos de 5.5 ñ'}, ensure_ascii=False).encode('utf-8')
        open(os.path.join(d, 'pronostico_dia.json'), 'wb').write(original)
        assert cajon.cerrar(d, 'clave de prueba') == 0
        cifrado = open(cajon.ruta_cajon('pronostico_dia.json', d), 'rb').read()
        assert b'Menos de' not in cifrado and cifrado[:8] == b'Salted__'
        os.remove(os.path.join(d, 'pronostico_dia.json'))
        assert cajon.abrir(d, False, 'clave de prueba') == 0
        assert open(os.path.join(d, 'pronostico_dia.json'), 'rb').read() == original
    finally:
        shutil.rmtree(d)


def test_sin_cambios_no_se_reescribe():
    d = _dir()
    try:
        open(os.path.join(d, 'anunciadas_dia.json'), 'wb').write(b'{}')
        cajon.cerrar(d, 'k')
        antes = open(cajon.ruta_cajon('anunciadas_dia.json', d), 'rb').read()
        cajon.cerrar(d, 'k')
        assert open(cajon.ruta_cajon('anunciadas_dia.json', d), 'rb').read() == antes     # la sal lo cambiaría: sería un commit por pasada
        open(os.path.join(d, 'anunciadas_dia.json'), 'wb').write(b'{"a":1}')
        cajon.cerrar(d, 'k')
        assert open(cajon.ruta_cajon('anunciadas_dia.json', d), 'rb').read() != antes
    finally:
        shutil.rmtree(d)


def test_clave_equivocada_o_ausente():
    d = _dir()
    try:
        open(os.path.join(d, 'pronostico_dia.json'), 'wb').write(b'{}')
        cajon.cerrar(d, 'buena')
        os.remove(os.path.join(d, 'pronostico_dia.json'))
        assert cajon.abrir(d, True, 'mala') == 1                       # el sitio no publica sin sus datos
        assert not os.path.exists(os.path.join(d, 'pronostico_dia.json'))
        assert cajon.abrir(d, False, 'mala') == 0                      # los demás flujos siguen, con aviso
    finally:
        shutil.rmtree(d)


def test_en_git_no_estan_en_claro():
    versionados = subprocess.check_output(['git', 'ls-files'], cwd=RAIZ).decode('utf-8', 'replace').split('\n')
    for x in cajon.ARCHIVOS:
        assert x not in versionados, x + ' sigue versionado en claro'
        assert 'cajon/%s.gz.enc' % x in versionados, x + ' no está en el cajón'
        assert x in leer('.gitignore')


def test_flujos():
    pre = leer('.github', 'workflows', 'precalculo_dia.yml')
    assert 'python cajon.py cerrar' in pre and 'for _f in cajon ' in pre
    linea = next(l for l in pre.splitlines() if 'for _f in cajon ' in l)
    for x in cajon.ARCHIVOS:
        assert x not in linea, x + ' volvería a subirse en claro'
    assert pre.index('cajon.py abrir --estricto') < pre.index('pronostico_dia.json')  # la guarda de frescura lo lee
    assert 'cajon.py abrir --estricto' in leer('.github', 'workflows', 'sitio_web.yml')
    for w in ['retrain_leagues', 'recalibrar', 'radar_diario', 'telegram_bot', 'telegram_dia_completo', 'cuotas_mx', 'precalcular_rosters',
              'validate_sharpicks', 'test_sharpicks_v402']:
        y = leer('.github', 'workflows', w + '.yml')
        assert 'cajon.py abrir' in y and 'secrets.DATOS_CLAVE' in y, w
        assert y.index('actions/checkout') < y.index('cajon.py abrir'), w


def test_borrar_cuenta():
    f = leer('supabase', 'functions', 'borrar-cuenta', 'index.ts')
    assert f.index('cancelarCobro(String(s.id))') < f.index('auth.admin.deleteUser')      # primero se deja de cobrar
    assert 'pf?.admin' in f and 'confirmar !== true' in f
    assert "'authorized', 'pending', 'cancela_al_final'" in f
    assert 'banChatMember' in f                                                           # nadie lo sacaría del grupo VIP después
    assert 'on delete set null' in leer('supabase', 'v584_borrar_cuenta.sql')             # la compra queda, sin identificar
    c = leer('web', 'cuenta.js')
    assert 'data-borrar-cuenta' in c and "[data-borrar-cuenta]" in c and "FN + 'borrar-cuenta'" in c
    assert '(esAdmin() ? \'\' : \'<button class="salir borrar-cuenta"' in c


def test_renovacion_con_consentimiento_expreso():
    c = leer('web', 'cuenta.js')
    assert '<input type="checkbox" id="vip-renovar">' in c and 'id="vip-renovar" checked' not in c


def test_registro_con_consentimiento_expreso():
    h = leer('web', 'index.html')
    assert '<input type="checkbox" id="c-acepto">' in h and 'Soy mayor de 18 años' in h
    assert 'id="c-acepto"> <span>Soy mayor' in h and 'checked' not in h[h.index('id="c-acepto"') - 30:h.index('id="c-acepto"') + 20]
    c = leer('web', 'cuenta.js')
    assert "!$('c-acepto').checked" in c and 'acepto_terminos: new Date().toISOString()' in c
    assert c.index("!$('c-acepto').checked") < c.index('sb.auth.signUp(')


def test_legales_al_dia_y_en_dos_idiomas():
    for pag in ('privacidad.html', 'terminos.html'):
        h = leer('web', pag)
        assert 'data-lang="es"' in h and 'data-lang="en" hidden' in h and 'legal.js' in h
        assert 'sharpicks.bet@gmail.com' in h and '6 de noviembre de 2026' in h and 'November 6, 2026' in h
    p = leer('web', 'privacidad.html')
    assert 'no guardamos contraseñas' not in p
    for x in ['Stripe', 'Mercado Pago', 'Cloudflare', 'Brevo', 'Telegram', 'Supabase', 'GitHub', 'Borrar mi cuenta', '20 días', '15 días']:
        assert x in p, x
    t = leer('web', 'terminos.html')
    assert 'Profeco' in t and '7 días antes de cada cobro' in t and 'Cancelar renovación' in t
    assert 'node --check web/legal.js' in leer('.github', 'workflows', 'sitio_web.yml')


def test_los_registros_publicos_no_imprimen_picks():
    # 6-nov: 5 picks premium por jugar se leían en el registro de «Bot Telegram - Día completo»
    for a in ('bot_dia_completo.py', 'bot_telegram.py'):
        assert "os.environ.get('GITHUB_ACTIONS')" in leer(a) and 'oculto en el registro público' in leer(a), a
    import contextlib
    import bot_dia_completo as b
    salida = io.StringIO()
    antes = os.environ.get('GITHUB_ACTIONS')
    os.environ['GITHUB_ACTIONS'] = 'true'
    try:
        with contextlib.redirect_stdout(salida):
            b._imprimir('Goles: Menos de 5.5')
    finally:
        if antes is None:
            del os.environ['GITHUB_ACTIONS']
        else:
            os.environ['GITHUB_ACTIONS'] = antes
    assert 'Menos de' not in salida.getvalue() and 'oculto' in salida.getvalue()


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
