#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v526 — LA TARJETA DE TELEGRAM: un «ticket» en imagen para el pick del día, la combinada y los picks VIP.

El usuario: «hay grupos donde mandan este tipo de cosas (un ticket de la casa); si podemos enviar algo así, más
visual y atractivo, estaría padre… breves pero impactantes». Se dibuja con Pillow (viene con matplotlib) y la
fuente DejaVu que trae matplotlib, para que salga igual en el servidor de GitHub y en la PC.

  ticket(titulo, patas, etiqueta='VIP')  → bytes PNG
    patas: [{'partido', 'apuesta', 'cuota', 'prob', 'cuando'}] (hasta 6)

v548 — el usuario: «en lugar de $100 úsalo como si estuvieras apostando 10,000, a veces 5,000 o cifras arriba de 5,000
y menos de 20,000». La apuesta del ejemplo sale de MONTOS (casi siempre 10,000) y es la misma para el mismo ticket.
Y para el canal gratis: `censurado=True` deja ver el partido y la hora, pero el pick, la cuota, el % y lo que se gana
salen borrosos (se dibuja un texto de relleno, nunca el real) con la franja «Sólo VIP».
"""
import hashlib
import io
import os
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

MONTOS = (10000, 10000, 10000, 5000, 7500, 12000, 15000, 18000)


def monto(patas: List[Dict]) -> int:
    """La apuesta del ejemplo: entre 5,000 y 19,999, casi siempre 10,000, fija para el mismo ticket."""
    clave = '|'.join('%s|%s' % (p.get('partido'), p.get('apuesta')) for p in patas).encode('utf-8')
    return MONTOS[int(hashlib.md5(clave).hexdigest(), 16) % len(MONTOS)]


def _pesos(n: float) -> str:
    return '$' + format(int(round(n)), ',')


def _borroso(im: Image.Image, caja, dibujar) -> None:
    """Dibuja algo en una capa aparte y la pega muy borrosa en `caja` (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = caja
    capa = im.crop(caja)
    dibujar(ImageDraw.Draw(capa))
    im.paste(capa.filter(ImageFilter.GaussianBlur(14)), (x0, y0))

AQUI = os.path.dirname(os.path.abspath(__file__))
ANCHO = 1080
FONDO, CAJA, BORDE = (9, 13, 28), (20, 26, 51), (44, 54, 92)
VERDE, VERDE_OSC, BLANCO, TENUE, ORO = (61, 220, 132), (22, 120, 72), (240, 244, 255), (150, 160, 190), (250, 204, 21)


def _fuente(tam: int, negrita: bool = True) -> ImageFont.FreeTypeFont:
    nombres = ['DejaVuSans-Bold.ttf' if negrita else 'DejaVuSans.ttf']
    try:
        import matplotlib
        base = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')
        nombres = [os.path.join(base, n) for n in nombres] + nombres
    except Exception:
        pass
    nombres += ['/usr/share/fonts/truetype/dejavu/' + ('DejaVuSans-Bold.ttf' if negrita else 'DejaVuSans.ttf'),
                'C:/Windows/Fonts/' + ('arialbd.ttf' if negrita else 'arial.ttf')]
    for n in nombres:
        try:
            return ImageFont.truetype(n, tam)
        except Exception:
            continue
    return ImageFont.load_default()


def _corta(d: ImageDraw.ImageDraw, txt: str, f, ancho: int) -> str:
    txt = str(txt or '')
    if d.textlength(txt, font=f) <= ancho:
        return txt
    while txt and d.textlength(txt + '…', font=f) > ancho:
        txt = txt[:-1]
    return txt + '…'


def ticket(titulo: str, patas: List[Dict], etiqueta: str = 'VIP', pie: Optional[str] = None, censurado: bool = False) -> bytes:
    patas = patas[:6]
    apuesta = monto(patas)
    fila_h, cab_h, pie_h = 190, 200, 150 if len(patas) > 1 or censurado else 110
    alto = cab_h + fila_h * len(patas) + pie_h + 40
    im = Image.new('RGB', (ANCHO, alto), FONDO)
    d = ImageDraw.Draw(im)
    # un brillo verde arriba (como el vidrio de la app)
    for i in range(160):
        a = int(40 * (1 - i / 160))
        d.line([(0, i), (ANCHO, i)], fill=(9 + a // 6, 13 + a // 2, 28 + a // 5))
    d.rounded_rectangle([30, 30, ANCHO - 30, alto - 30], radius=36, fill=CAJA, outline=BORDE, width=3)
    # cabecera: logo, marca, título y la etiqueta (VIP / GRATIS)
    x = 70
    try:
        logo = Image.open(os.path.join(AQUI, 'web', 'marca', 'logo-96.png')).convert('RGBA').resize((84, 84))
        im.paste(logo, (x, 62), logo)
        x += 104
    except Exception:
        pass
    d.text((x, 64), 'Shar', font=_fuente(40), fill=BLANCO)
    d.text((x + d.textlength('Shar', font=_fuente(40)), 64), 'Picks', font=_fuente(40), fill=VERDE)
    d.text((x, 112), _corta(d, titulo.upper(), _fuente(30), 560), font=_fuente(30), fill=TENUE)
    fe = _fuente(30)
    ew = d.textlength(etiqueta, font=fe) + 44
    color = ORO if etiqueta.upper() == 'VIP' else VERDE
    d.rounded_rectangle([ANCHO - 70 - ew, 74, ANCHO - 70, 128], radius=27, fill=color)
    d.text((ANCHO - 70 - ew + 22, 82), etiqueta, font=fe, fill=FONDO)
    y = cab_h
    cuota_total, prob_total = 1.0, 1.0
    for p in patas:
        cuota, prob = float(p.get('cuota') or 0), float(p.get('prob') or 0)
        cuota_total *= cuota or 1
        prob_total *= prob or 1
        d.line([(70, y - 10), (ANCHO - 70, y - 10)], fill=BORDE, width=2)
        d.text((70, y + 4), _corta(d, '%s · %s' % (p.get('partido', ''), p.get('cuando', '')), _fuente(28, False), 700), font=_fuente(28, False), fill=TENUE)
        fc = _fuente(46)
        if censurado:
            # nada real: texto de relleno, borroso, y la etiqueta «Sólo VIP» encima
            _borroso(im, (60, y + 36, 800, y + 150), lambda c: (
                c.text((10, 8), 'Gana XXXXXX XXXXXXX', font=_fuente(42), fill=BLANCO),
                c.rounded_rectangle([10, 80, 610, 98], radius=9, fill=VERDE)))
            _borroso(im, (ANCHO - 250, y + 10, ANCHO - 60, y + 100), lambda c: (
                c.rounded_rectangle([20, 8, 180, 82], radius=18, fill=VERDE_OSC), c.text((45, 17), '1.XX', font=fc, fill=BLANCO)))
            fv = _fuente(30)
            tv = 'SÓLO VIP'
            tw = d.textlength(tv, font=fv) + 40
            d.rounded_rectangle([ANCHO - 70 - tw, y + 108, ANCHO - 70, y + 152], radius=22, fill=ORO)
            d.text((ANCHO - 70 - tw + 20, y + 114), tv, font=fv, fill=FONDO)
            y += fila_h
            continue
        d.text((70, y + 44), _corta(d, p.get('apuesta', ''), _fuente(42), 700), font=_fuente(42), fill=BLANCO)
        # la cuota en su caja verde, a la derecha
        ct = '%.2f' % cuota
        cw = d.textlength(ct, font=fc) + 50
        d.rounded_rectangle([ANCHO - 70 - cw, y + 18, ANCHO - 70, y + 92], radius=18, fill=VERDE_OSC)
        d.text((ANCHO - 70 - cw + 25, y + 27), ct, font=fc, fill=BLANCO)
        # la barra de probabilidad
        d.rounded_rectangle([70, y + 116, 70 + 600, y + 134], radius=9, fill=(36, 44, 78))
        d.rounded_rectangle([70, y + 116, 70 + int(600 * min(prob, 1)), y + 134], radius=9, fill=VERDE)
        d.text((690, y + 106), '%d %%' % round(100 * prob), font=_fuente(32), fill=VERDE)
        y += fila_h
    d.line([(70, y - 10), (ANCHO - 70, y - 10)], fill=BORDE, width=2)
    tx = '%s  →  %s' % (_pesos(apuesta), _pesos(apuesta * cuota_total))
    if censurado:
        # lo que se gana también, borroso; encima, cómo desbloquearlo
        d.text((70, y + 6), 'Cuota total y ganancia', font=_fuente(30, False), fill=TENUE)
        _borroso(im, (60, y + 40, ANCHO - 60, y + 110), lambda c: c.text((10, 8), '%s  →  $XX,XXX     X.XX' % _pesos(apuesta), font=_fuente(44), fill=BLANCO))
        msg = 'Desbloquéalo con VIP en sharpicksapp.com'
        d.text(((ANCHO - d.textlength(msg, font=_fuente(30))) / 2, y + 62), msg, font=_fuente(30), fill=ORO)
    elif len(patas) > 1:
        d.text((70, y + 6), 'Cuota total', font=_fuente(30, False), fill=TENUE)
        d.text((70, y + 44), '%.2f' % cuota_total, font=_fuente(52), fill=VERDE)
        d.text((ANCHO - 70 - d.textlength(tx, font=_fuente(40)), y + 52), tx, font=_fuente(40), fill=BLANCO)
    else:
        d.text((70, y + 10), tx, font=_fuente(40), fill=BLANCO)
    d.text((70, alto - 78), pie or 'sharpicksapp.com  ·  +18  ·  juega con responsabilidad', font=_fuente(24, False), fill=TENUE)
    out = io.BytesIO()
    im.save(out, 'PNG', optimize=True)
    return out.getvalue()


if __name__ == '__main__':
    demo = [{'partido': 'América vs Tijuana', 'cuando': 'HOY 19:00', 'apuesta': 'Gana América', 'cuota': 1.25, 'prob': 0.82},
            {'partido': 'Fiorentina vs Atalanta', 'cuando': 'HOY 13:45', 'apuesta': 'Más de 1.5 goles', 'cuota': 1.18, 'prob': 0.86}]
    open('ticket_demo.png', 'wb').write(ticket('Combinada del día', demo, 'GRATIS'))
    open('ticket_demo_vip.png', 'wb').write(ticket('Pick VIP', demo[:1], 'VIP'))
    open('ticket_demo_censurado.png', 'wb').write(ticket('Picks VIP · ya es hora', demo, 'VIP', censurado=True))
    print('listo')
