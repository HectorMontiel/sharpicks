#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v594 — la foto de precios: apagada no cambia nada; encendida no toca la red de esas dos fuentes."""
import json
import os
import tarfile
import tempfile
import time

import cuotas_multi as cm
import foto_precios as fp

_fallos = []


def ok(nombre, cond):
    print(('OK   ' if cond else 'FALLA') + ' ' + nombre)
    if not cond:
        _fallos.append(nombre)


class _Resp:
    def raise_for_status(self):
        pass

    def json(self):
        return {'dato': 1}


llamadas = []
original = cm.requests.get
cm.requests.get = lambda *a, **k: (llamadas.append(a[0]), _Resp())[1]
carpeta_original = cm.CACHE_DIR
ttl0, gr0 = cm.FOTO_TTL, cm.FOTO_GRABAR
with tempfile.TemporaryDirectory() as tmp:
    cm.CACHE_DIR = tmp
    url_pin = cm.PIN_BASE + '/sports/29/matchups'
    url_pdt = 'https://sb2frontend-altenar2.biahosted.com/api/widget/GetEvents'
    url_otra = 'https://www.bovada.lv/x'

    # Apagada: va a la red y no graba
    cm.FOTO_TTL, cm.FOTO_GRABAR = 0, False
    ok('apagada: consulta la red', cm._get(url_pin, {'brandId': 0}) == {'dato': 1} and llamadas == [url_pin])
    ok('apagada: no graba', not os.listdir(tmp))

    # Grabando (GitHub): guarda Pinnacle
    cm.FOTO_GRABAR = True
    cm._get(url_pin, {'brandId': 0})
    ok('grabando: guarda la respuesta', os.path.exists(cm._cache_path(cm._foto_clave(url_pin, {'brandId': 0}))))
    cm.FOTO_GRABAR = False

    # Servidor: lee la foto, sin red
    llamadas.clear()
    cm.FOTO_TTL = 3600
    ok('servidor: lee la foto', cm._get(url_pin, {'brandId': 0}) == {'dato': 1})
    ok('servidor: otra consulta sin foto da None', cm._get(url_pin, {'brandId': 1}) is None)
    ok('servidor: Playdoit sin foto da None', cm._get(url_pdt, {'sportid': 66}) is None)
    ok('servidor: nunca fue a la red por esas dos', llamadas == [])
    cm._get(url_otra)
    ok('servidor: las demás fuentes sí van a la red', llamadas == [url_otra])

    # Vigencia: la foto vieja caduca; las otras cachés siguen en 30 min
    p = cm._cache_path('playdoit_futbol.json')
    json.dump({'a': 1}, open(p, 'w'))
    q = cm._cache_path('bovada_futbol.json')
    json.dump({'a': 1}, open(q, 'w'))
    hace = time.time() - 2400
    os.utime(p, (hace, hace))
    os.utime(q, (hace, hace))
    ok('la foto vale su vigencia completa', cm._leer_cache('playdoit_futbol.json') == {'a': 1})
    ok('Bovada sigue con su TTL corto', cm._leer_cache('bovada_futbol.json') is None)
    hace = time.time() - 4000
    os.utime(p, (hace, hace))
    ok('la foto caducada no se usa', cm._leer_cache('playdoit_futbol.json') is None)

    # Desempacar: conserva la edad y no deja salir de la carpeta
    paq = os.path.join(tmp, 'p.tar.gz')
    fuente = os.path.join(tmp, 'playdoit_nba.json')
    json.dump({'b': 2}, open(fuente, 'w'))
    edad = time.time() - 500
    os.utime(fuente, (edad, edad))
    malo = os.path.join(tmp, 'malo.json')
    json.dump({}, open(malo, 'w'))
    with tarfile.open(paq, 'w:gz') as t:
        t.add(fuente, arcname='playdoit_nba.json')
        t.add(malo, arcname='../playdoit_fuera.json')
        t.add(malo, arcname='otra_cosa.json')
    destino = os.path.join(tmp, 'd')
    ok('desempacar: sólo lo esperado', fp.desempacar(paq, destino) == 1 and os.listdir(destino) == ['playdoit_nba.json'])
    ok('desempacar: conserva la edad', abs(os.path.getmtime(os.path.join(destino, 'playdoit_nba.json')) - edad) < 3)

    # Con la foto vencida no se cocina: medido, salen 0 de Capa 1
    def _con_edad(minutos):
        with open(os.path.join(cm.CACHE_DIR, fp.META), 'w', encoding='utf-8') as f:
            json.dump({'generado': time.time() - minutos * 60}, f)

    cm.CACHE_DIR = tempfile.mkdtemp()
    cm.FOTO_TTL = 0
    ok('vencida: sin la variable, nunca (GitHub sigue igual)', not fp.vencida())
    cm.FOTO_TTL = 14400
    ok('vencida: sin foto, sí', fp.vencida())
    _con_edad(120)
    ok('vencida: de 2 h, no', not fp.vencida())
    _con_edad(230)
    ok('vencida: si caduca antes de terminar, sí', fp.vencida())

cm.CACHE_DIR, cm.FOTO_TTL, cm.FOTO_GRABAR = carpeta_original, ttl0, gr0
cm.requests.get = original

# El flujo sólo se lanza a mano hasta que se autorice el cron
texto = open('.github/workflows/foto_precios.yml', encoding='utf-8').read()
ok('flujo: sin cron', 'schedule' not in texto and 'workflow_dispatch' in texto)
ok('flujo: no publica fuera del release', 'git push' not in texto and 'foto-precios' in texto)

print('\n%d fallos' % len(_fallos))
raise SystemExit(1 if _fallos else 0)
