#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v592 — EL PAQUETE FISCAL DEL MES (persona física en RESICO).

Sale del libro `pagos`: lo cobrado, el IVA y el ISR ya calculados, los montos a capturar en el portal del SAT y los datos de la
factura global. Llega por correo y por Telegram al administrador. Nunca se imprime un monto en el registro del flujo, que es público.

Está apagado: sólo corre con FISCAL_ACTIVO=1. Tabla de ISR: LISR art. 113-E. Es un cálculo de apoyo: quien presenta es el contribuyente.
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

TABLA_ISR = ((25000.0, .01), (50000.0, .011), (83333.33, .015), (208333.33, .02), (float('inf'), .025))
LIMITE_ANUAL = 3500000.0
IVA = .16
CDMX = dt.timezone(dt.timedelta(hours=-6))


def tasa_isr(ingreso_mes: float) -> float:
    return next(t for tope, t in TABLA_ISR if ingreso_mes <= tope)


def comision_de(p: Dict) -> Tuple[float, bool]:
    """(comisión, si es estimada). Si la pasarela no la informó se estima con la tarifa de Stripe en México: 3,6 % + $3, más IVA."""
    if p.get('comision') is not None:
        return float(p['comision']), False
    return round((float(p['bruto']) * .036 + 3) * 1.16, 2), True


def mes_de(p: Dict) -> str:
    return dt.datetime.fromisoformat(str(p['pagado']).replace('Z', '+00:00')).astimezone(CDMX).strftime('%Y-%m')


def resumen(pagos: List[Dict], mes: str) -> Dict:
    del_mes = [p for p in pagos if mes_de(p) == mes]
    cobrado = sum(float(p['bruto']) - float(p.get('reembolsado') or 0) for p in del_mes)
    base = cobrado / (1 + IVA)
    iva = cobrado - base
    com = [comision_de(p) for p in del_mes]
    comisiones = sum(c for c, _ in com)
    iva_comisiones = comisiones * IVA / (1 + IVA)
    tasa = tasa_isr(base)
    acumulado = sum((float(p['bruto']) - float(p.get('reembolsado') or 0)) / (1 + IVA) for p in pagos if mes_de(p)[:4] == mes[:4] and mes_de(p) <= mes)
    por_dia: Dict[str, List[float]] = {}
    for p in del_mes:
        d = dt.datetime.fromisoformat(str(p['pagado']).replace('Z', '+00:00')).astimezone(CDMX).strftime('%Y-%m-%d')
        x = por_dia.setdefault(d, [0, 0.0])
        x[0] += 1
        x[1] += float(p['bruto']) - float(p.get('reembolsado') or 0)
    por_tipo: Dict[str, List[float]] = {}
    for p in del_mes:
        x = por_tipo.setdefault(str(p.get('tipo')), [0, 0.0])
        x[0] += 1
        x[1] += float(p['bruto']) - float(p.get('reembolsado') or 0)
    return {'mes': mes, 'operaciones': len(del_mes), 'cobrado': cobrado, 'base': base, 'iva': iva, 'tasa': tasa, 'isr': base * tasa, 'comisiones': comisiones,
            'iva_comisiones': iva_comisiones, 'iva_a_pagar': max(0.0, iva - iva_comisiones), 'estimadas': sum(1 for _, e in com if e), 'acumulado': acumulado,
            'por_dia': por_dia, 'por_tipo': por_tipo, 'neto': cobrado - iva - base * tasa - (comisiones - iva_comisiones)}


def fecha_limite(mes: str) -> str:
    a, m = int(mes[:4]), int(mes[5:7])
    a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return '%d-%02d-17' % (a, m)


def _d(x: float) -> str:
    return '${:,.2f}'.format(x)


def documento(r: Dict, vencido: bool = False) -> str:
    fila = lambda a, b: '<tr><td>%s</td><td style="text-align:right"><b>%s</b></td></tr>' % (html.escape(a), html.escape(b))
    t = ['<!doctype html><meta charset="utf-8"><title>SharPicks · %s</title><body style="font-family:Arial,sans-serif;max-width:720px;margin:auto;color:#111;line-height:1.45">' % r['mes'],
         '<h1>Paquete fiscal de %s</h1><p>RESICO persona física. Fecha límite: <b>%s</b>. Es un cálculo de apoyo: revisa que coincida con lo que precarga el SAT.</p>' % (r['mes'], fecha_limite(r['mes']))]
    if vencido:
        t.append('<p style="color:#b00"><b>Este mes ya venció.</b> El portal del SAT suma la actualización y los recargos al presentarla.</p>')
    t += ['<h2>1. Lo que capturas en el SAT</h2><table style="width:100%;border-collapse:collapse">',
          fila('Ingresos cobrados sin IVA', _d(r['base'])), fila('ISR a pagar (%.2f %%)' % (100 * r['tasa']), _d(r['isr'])),
          fila('IVA cobrado (16 %)', _d(r['iva'])), fila('IVA acreditable de comisiones (si tienes su factura)', _d(r['iva_comisiones'])),
          fila('IVA a pagar', _d(r['iva_a_pagar'])), fila('Total a pagar al SAT', _d(r['isr'] + r['iva_a_pagar'])), '</table>',
          '<h2>2. Factura global al público en general</h2><table style="width:100%;border-collapse:collapse">',
          fila('Operaciones', str(r['operaciones'])), fila('Subtotal', _d(r['base'])), fila('IVA 16 %', _d(r['iva'])), fila('Total', _d(r['cobrado'])), '</table>',
          '<h2>3. Estado del mes</h2><table style="width:100%;border-collapse:collapse">', fila('Cobrado a clientes', _d(r['cobrado'])),
          fila('Comisiones de pago', _d(r['comisiones'])), fila('Te queda después de impuestos y comisiones', _d(r['neto'])),
          fila('Acumulado del año sin IVA (tope %s)' % _d(LIMITE_ANUAL), _d(r['acumulado'])), '</table>', '<h2>4. Por tipo</h2><table style="width:100%;border-collapse:collapse">']
    t += [fila('%s (%d)' % (k, int(v[0])), _d(v[1])) for k, v in sorted(r['por_tipo'].items())]
    t.append('</table><h2>5. Por día</h2><table style="width:100%;border-collapse:collapse">')
    t += [fila('%s (%d)' % (k, int(v[0])), _d(v[1])) for k, v in sorted(r['por_dia'].items())]
    t.append('</table>')
    if r['estimadas']:
        t.append('<p>%d comisiones son estimadas: la pasarela no informó el monto exacto.</p>' % r['estimadas'])
    t.append('<p>Las devoluciones hechas directo en Stripe o Mercado Pago deben anotarse en el libro de pagos para que se resten.</p></body>')
    return ''.join(t)


def _api(metodo: str, url: str, h: Dict, cuerpo: Optional[Dict] = None):
    r = urllib.request.Request(url, method=metodo, headers=h, data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    with urllib.request.urlopen(r, timeout=60) as f:
        t = f.read()
    return json.loads(t) if t else None


def _todas(base: str, h: Dict, tabla: str, q: str) -> List[Dict]:
    filas = []
    for i in range(200):
        lote = _api('GET', '%s/%s?%s&limit=1000&offset=%d' % (base, tabla, q, i * 1000), h)
        filas += lote
        if len(lote) < 1000:
            break
    return filas


def enviar_correo(asunto: str, cuerpo: str, nombre: str, adjunto: str) -> bool:
    k, de = os.environ.get('BREVO_API_KEY'), os.environ.get('BREVO_REMITENTE')
    if not k or not de:
        return False
    try:
        _api('POST', 'https://api.brevo.com/v3/smtp/email', {'api-key': k, 'Content-Type': 'application/json', 'accept': 'application/json'},
             {'sender': {'name': 'SharPicks', 'email': de}, 'to': [{'email': de}], 'subject': asunto, 'htmlContent': cuerpo,
              'attachment': [{'name': nombre, 'content': base64.b64encode(adjunto.encode('utf-8')).decode()}]})
        return True
    except Exception as e:
        print('fiscal: correo %s' % type(e).__name__)
        return False


def meses_pendientes(pagos: List[Dict], hoy: dt.date, enviados: set) -> List[str]:
    ultimo = (hoy.replace(day=1) - dt.timedelta(days=1)).strftime('%Y-%m')
    return sorted({m for m in map(mes_de, pagos) if m <= ultimo and m not in enviados})


def main() -> int:
    if os.environ.get('FISCAL_ACTIVO') != '1':
        print('fiscal: apagado')
        return 0
    u, k = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1', os.environ['SUPABASE_SERVICE_KEY']
    h = {'apikey': k, 'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'sharpicks'}
    pagos = _todas(u, h, 'pagos', 'select=bruto,comision,reembolsado,pagado,tipo&order=pagado')
    enviados = {x['clave'] for x in _todas(u, h, 'fiscal_envios', 'select=clave&order=clave')}
    hoy = dt.datetime.now(CDMX).date()
    import vigia_limites as v
    for mes in meses_pendientes(pagos, hoy, enviados):
        r = resumen(pagos, mes)
        vencido = hoy.isoformat() > fecha_limite(mes)
        doc = documento(r, vencido)
        texto = 'Paquete fiscal de %s. Fecha límite: %s. Total a pagar al SAT: %s (ISR %s, IVA %s).' % (mes, fecha_limite(mes), _d(r['isr'] + r['iva_a_pagar']), _d(r['isr']), _d(r['iva_a_pagar']))
        if enviar_correo('SharPicks: ' + texto, '<p>%s</p><p>Va adjunto con todo el desglose.</p>' % html.escape(texto), 'paquete_fiscal_%s.html' % mes, doc):
            v.telegram('🧾 ' + texto + ' El desglose te llegó por correo. Sólo entra al SAT, confirma y paga.')
            _api('POST', u + '/fiscal_envios', dict(h, Prefer='return=minimal'), {'clave': mes})
            print('fiscal: enviado un mes')
    mes_ant = (hoy.replace(day=1) - dt.timedelta(days=1)).strftime('%Y-%m')
    clave = mes_ant + '|recordatorio'
    if 12 <= hoy.day <= 16 and mes_ant in {m.split('|')[0] for m in enviados} and clave not in enviados:
        v.telegram('🧾 Recordatorio: la declaración de %s vence el %s.' % (mes_ant, fecha_limite(mes_ant)))
        _api('POST', u + '/fiscal_envios', dict(h, Prefer='return=minimal'), {'clave': clave})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
