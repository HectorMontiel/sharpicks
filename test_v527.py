#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v527 — avisos personales por Telegram: ligar la cuenta con un código de un solo uso (el bot lo canjea), elegir
deportes / Pulso / un partido, y que cada quien reciba sólo lo suyo (lo VIP completo sólo al VIP). Sin red."""
import datetime as dt
import io
import os

import telegram_canales as tc

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
    ahora = dt.datetime(2026, 10, 30, 18, 0, tzinfo=dt.timezone.utc)
    ini = lambda h: (ahora + dt.timedelta(hours=h)).strftime('%Y-%m-%d %H:%M:%S')
    picks = [
        {'id': 'p1', 'partido': 'Lakers vs Celtics', 'deporte': 'NBA', 'apuesta': 'Gana Lakers', 'cuota': 1.3, 'prob': 0.75, 'estado': 'pendiente', 'inicio': ini(2)},
        {'id': 'p2', 'partido': 'Yankees vs Red Sox', 'deporte': 'MLB', 'apuesta': 'Gana Yankees', 'cuota': 1.25, 'prob': 0.81, 'estado': 'pendiente', 'inicio': ini(3), 'elige': True, 'premium': True},
        {'id': 'p3', 'partido': 'América vs Tijuana', 'deporte': 'Fútbol', 'apuesta': 'Gana América', 'cuota': 1.2, 'prob': 0.86, 'estado': 'pendiente', 'inicio': ini(1)},
        {'id': 'p4', 'partido': 'Lakers vs Celtics', 'deporte': 'NBA', 'apuesta': 'Más de 200', 'cuota': 1.3, 'prob': 0.75, 'estado': 'pendiente', 'inicio': ini(9)},
    ]
    destinos = [
        {'usuario': 'vip1', 'chat': 111, 'vip': True, 'tipo': 'deporte', 'valor': 'Béisbol'},
        {'usuario': 'gra1', 'chat': 222, 'vip': False, 'tipo': 'deporte', 'valor': 'Béisbol'},
        {'usuario': 'gra1', 'chat': 222, 'vip': False, 'tipo': 'deporte', 'valor': 'NBA'},
        {'usuario': 'par1', 'chat': 333, 'vip': False, 'tipo': 'partido', 'valor': tc.clave_partido(picks[2])},
    ]
    out = {c: (t, cubre) for c, t, cubre in tc.armar_personales(picks, destinos, set(), ahora)}
    check(set(out) == {111, 222, 333}, 'v527: cada quien recibe lo suyo (3 mensajes, uno por persona)')
    check('Gana Yankees' in out[111][0] and 'Lakers' not in out[111][0], 'v527: el VIP de béisbol recibe el pick de MLB completo (y no el de NBA)')
    check('Gana Yankees' not in out[222][0] and '🔒' in out[222][0] and 'Gana Lakers' in out[222][0],
          'v527: al gratis, lo VIP con candado y lo gratis completo')
    check('Más de 200' not in out[222][0], 'v527: sólo lo que ya está en hora de apostar (4 h)')
    check('América vs Tijuana' in out[333][0] and 'Gana América' not in out[333][0] and 'Pick Platino' in out[333][0],
          'v527: quien sigue un partido recibe sus picks (el 🔷 Platino, con candado si no es VIP)')
    check(tc.clave_partido(picks[2]) == 'Fútbol|américa / tijuana|2026-10-30', 'v527: la clave del partido es la de la página')
    ya = {c for _, _, cubre in tc.armar_personales(picks, destinos, set(), ahora) for c, _, _ in cubre}
    check(not tc.armar_personales(picks, destinos, ya, ahora), 'v527: lo ya mandado no se repite')
    # v530 — lo tuyo: el resultado de los picks que sigues y de tus combinadas
    ps = [dict(picks[0], estado='verde', marcador='2-1'), dict(picks[1], estado='pendiente')]
    lig = [{'usuario': 'u1', 'chat': 9}, {'usuario': 'u2', 'chat': 8}]
    seg = [{'usuario': 'u1', 'pick': 'p1'}, {'usuario': 'u1', 'pick': 'p2'}, {'usuario': 'u2', 'pick': 'p2'}]
    com = [{'id': 'c1', 'usuario': 'u2', 'cuota': 1.5, 'estado': 'verde', 'premio': 30}]
    mc = {c: t for c, t, _ in tc.armar_mis_cosas(ps, lig, seg, com, set())}
    check(set(mc) == {9, 8} and 'Gana Lakers' in mc[9] and 'Gana Yankees' not in mc[9] and 'combinada se cumplió' in mc[8] and '+30' in mc[8],
          'v530: a cada quien el resultado de SUS picks seguidos (sólo los ya decididos) y de SUS combinadas')
    ya2 = {k for _, _, cb in tc.armar_mis_cosas(ps, lig, seg, com, set()) for k, _, _ in cb}
    check(not tc.armar_mis_cosas(ps, lig, seg, com, ya2), 'v530: lo ya avisado no se repite')
    check("ventanaApp({ tipo: 'pregunta', titulo: 'Conecta tu Telegram'" in leer('web', 'cuenta.js') and 'alertaPendiente' in leer('web', 'cuenta.js'),
          'v530: sin Telegram, la campana ofrece conectarlo ahí mismo y el partido queda seguido al volver')
    check('class="campana-fila"' in leer('web', 'app.js') and 'pick-fila compacta' in leer('web', 'app.js'),
          'v530: la campana en su renglón (ámbar / verde) y cada pick en dos renglones')
    # v534 — lo comprado con monedas llega completo a quien lo compró (y a nadie más); el VIP se mira en el momento
    dz = [{'usuario': 'gra1', 'chat': 222, 'vip': False, 'tipo': 'deporte', 'valor': 'Béisbol'},
          {'usuario': 'gra2', 'chat': 444, 'vip': False, 'tipo': 'deporte', 'valor': 'Béisbol'}]
    o2 = {c: t for c, t, _ in tc.armar_personales(picks, dz, set(), ahora, {'gra1': {'p2'}})}
    check('Gana Yankees' in o2[222] and 'Gana Yankees' not in o2[444] and '🔒' in o2[444],
          'v534: el pick desbloqueado con monedas le llega completo SÓLO a quien lo compró')
    o3 = {c: t for c, t, _ in tc.armar_personales(picks, dz, set(), ahora, {}, True)}
    check('Gana Yankees' in o3[444], 'v534: con «premium_con_cuenta» prendido, completo para toda cuenta (la regla de la página)')
    bot = leer('supabase', 'functions', 'telegram-bot', 'index.ts')
    check("approveChatJoinRequest" in bot and "declineChatJoinRequest" in bot and 'Tu solicitud se queda esperando' in bot and "rpc/telegram_quien" in bot and "allowed_updates: ['message', 'chat_join_request']" in bot,
          'v534: el bot aprueba la entrada al grupo VIP sólo si la app dice que es VIP vigente')
    src = leer('telegram_canales.py')
    check("'getChatMember'" in src and "rpc/telegram_ligados" in src, 'v536: el barrido revisa a todos los ligados, no sólo a los que aprobó el bot')
    check('def revisar_vip(' in src and "'banChatMember'" in src and "'only_if_banned': True" in src and 'rpc/telegram_vip_vencidos' in src,
          'v534: a quien se le acaba el VIP lo saca del grupo (puede volver si renueva) y le avisa')
    cu2 = leer('web', 'cuenta.js')
    check('function vipReloj()' in cu2 and 'vipReloj() +' in cu2 and "d < 3 ? ' pronto' : ''" in cu2,
          'v535: junto a las monedas, la corona del VIP con lo que le queda (ámbar a 3 días o menos)')
    sq = leer('supabase', 'v527_alertas_telegram.sql')
    check('revoke all on public.telegram_usuarios from anon, authenticated' in sq and "interval '15 minutes'" in sq
          and 'grant execute on function public.alertas_destinos() to service_role' in sq,
          'v527: el chat de cada quien no lo ve nadie; el código dura 15 min; los destinos sólo con la llave de servicio')
    bot = leer('supabase', 'functions', 'telegram-bot', 'index.ts')
    check("req.headers.get('x-telegram-bot-api-secret-token') !== s.telegram_webhook" in bot and "m.chat.type !== 'private'" in bot
          and 'codigo_hasta' in bot and '/stop' in bot, 'v527: el bot sólo atiende a Telegram firmado, en privado, con código vigente; /stop')
    nube = leer('supabase', 'functions', 'pulso-vivo', 'index.ts')
    check('avisosPersonales(p, e, clave, nuevas)' in nube and 'd.vip || abiertos.has(uid)' in nube,
          'v527: el Pulso avisa a quien sigue el partido o el Pulso (completo al VIP o a quien lo abrió)')
    cu, app = leer('web', 'cuenta.js'), leer('web', 'app.js')
    check("sb.rpc('telegram_codigo')" in cu and "'?start='" in cu and 'data-tg-al' in cu and 'pintarAvisosTg' in cu,
          'v527: Mi cuenta liga Telegram y elige qué avisar')
    check('data-tg-partido' in app and "ico('bell')" in app, 'v527: la campana en Ver partido')


if __name__ == '__main__':
    probar()
    print('\n' + '=' * 40)
    print('TODO OK' if not FALLOS else '%d FALLOS' % len(FALLOS))
    raise SystemExit(1 if FALLOS else 0)
