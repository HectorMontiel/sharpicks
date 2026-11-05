"""v562 — el Pulso ya no manda a los grupos de Telegram. Sigue midiendo y sigue el aviso privado a quien lo pidió."""
import io
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def fuente():
    return io.open(os.path.join(RAIZ, 'supabase', 'functions', 'pulso-vivo', 'index.ts'), encoding='utf-8').read()


def test_grupos_apagados():
    s = fuente()
    assert 'const AVISOS_A_GRUPOS = false;' in s
    corte = s.index('if (!AVISOS_A_GRUPOS) continue;')
    # los dos envíos a grupos quedan después del corte
    assert corte < s.index("enviar(textoGancho(p, e, m), 'gratis')") and corte < s.index('enviar(textoAviso(p, e, m, rec))')


def test_lo_medible_y_lo_privado_siguen():
    s = fuente()
    corte = s.index('if (!AVISOS_A_GRUPOS) continue;')
    assert s.index("await sbPost('pulso_senales', fila)") < corte            # la señal se apunta
    assert s.index('await avisosPersonales(p, e, clave, nuevas)') < corte    # el aviso privado sale
    assert s.index('await preguntarIA(p, e, opciones)') < corte              # la IA sigue para la página
    assert s.index("calificar('pulso_senales', x, e)") < corte               # y se califica


def test_el_aviso_personal_va_al_chat_de_cada_usuario():
    s = fuente()
    a = s[s.index('async function avisosPersonales'):s.index('// ---------- una vuelta')]
    assert 'chat_id: d.chat' in a and 'TELEGRAM_CHAT_VIP' not in a and 'TELEGRAM_CHAT_GRATIS' not in a


if __name__ == '__main__':
    for _n, _f in sorted(globals().copy().items()):
        if _n.startswith('test_') and callable(_f):
            _f()
    print('OK')
