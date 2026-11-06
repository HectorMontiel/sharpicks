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
Y para el canal gratis: `censurado=True` deja ver el partido y la hora; la jugada y su % salen borrosos (se dibuja un
texto de relleno, nunca el real) con la franja «Sólo VIP».
v563 — el usuario: «la cuota y la ganancia total no deben estar censuradas: eso es lo que hace que quieran comprar el VIP».
Y `ganado()`: la foto de cuando el parley se cumple, llamativa, con lo que se ganó.
"""
import hashlib
import io
import os
import random
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


def ticket(titulo: str, patas: List[Dict], etiqueta: str = 'VIP', pie: Optional[str] = None, censurado: bool = False,
           apuesta: Optional[int] = None) -> bytes:
    patas = patas[:6]
    apuesta = apuesta or monto(patas)
    fila_h, cab_h, pie_h = 190, 200, 205 if censurado else 150 if len(patas) > 1 else 110
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
            # la jugada no es real: texto de relleno, borroso, y la etiqueta «Sólo VIP»; la cuota sí se ve
            _borroso(im, (60, y + 36, 760, y + 150), lambda c: (
                c.text((10, 8), 'Gana XXXXXX XXXXXXX', font=_fuente(42), fill=BLANCO),
                c.rounded_rectangle([10, 80, 610, 98], radius=9, fill=VERDE)))
            if cuota:
                ct = '%.2f' % cuota
                cw = d.textlength(ct, font=fc) + 50
                d.rounded_rectangle([ANCHO - 70 - cw, y + 18, ANCHO - 70, y + 92], radius=18, fill=VERDE_OSC)
                d.text((ANCHO - 70 - cw + 25, y + 27), ct, font=fc, fill=BLANCO)
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
        # v563 — la cuota total y lo que se gana, a la vista; lo escondido es la jugada
        d.text((70, y + 6), 'Cuota total', font=_fuente(30, False), fill=TENUE)
        d.text((70, y + 44), '%.2f' % cuota_total, font=_fuente(52), fill=VERDE)
        d.text((ANCHO - 70 - d.textlength(tx, font=_fuente(40)), y + 52), tx, font=_fuente(40), fill=BLANCO)
        msg = 'Desbloquéalo con VIP en sharpicksapp.com'
        d.text(((ANCHO - d.textlength(msg, font=_fuente(30))) / 2, y + 116), msg, font=_fuente(30), fill=ORO)
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


def ganado(titulo: str, patas: List[Dict], apuesta: int, cuota_total: float, etiqueta: str = 'VIP', aprox: bool = False) -> bytes:
    """v563 — «cuando se cumplan esas apuestas, mandar que se cumplió y la ganancia; llamativo, que se note que ganaste».
    patas: [{'partido', 'apuesta', 'marcador'}] (hasta 6). `aprox`: el parley del mismo partido se calcula multiplicando
    cuotas y el Constructor puede pagar menos: las cifras llevan «~»."""
    ap = '~' if aprox else ''
    patas = patas[:6]
    fila_h, cab_h = 118, 330
    alto = cab_h + fila_h * len(patas) + 340
    im = Image.new('RGB', (ANCHO, alto), (6, 30, 20))
    d = ImageDraw.Draw(im)
    for i in range(alto):                       # fondo verde que se apaga hacia abajo
        t = i / alto
        d.line([(0, i), (ANCHO, i)], fill=(int(10 + 4 * t), int(70 - 50 * t), int(44 - 22 * t)))
    azar = random.Random('|'.join(str(p.get('apuesta')) for p in patas))
    for _ in range(90):                         # confeti, siempre igual para el mismo ticket
        x, y, r = azar.randint(0, ANCHO), azar.randint(0, alto), azar.randint(4, 10)
        d.ellipse([x - r, y - r, x + r, y + r], fill=azar.choice([ORO, VERDE, BLANCO, (96, 165, 250), (244, 114, 182)]))
    d.rounded_rectangle([30, 30, ANCHO - 30, alto - 30], radius=36, fill=(13, 26, 40), outline=VERDE, width=6)
    x = 70
    try:
        logo = Image.open(os.path.join(AQUI, 'web', 'marca', 'logo-96.png')).convert('RGBA').resize((76, 76))
        im.paste(logo, (x, 58), logo)
        x += 94
    except Exception:
        pass
    d.text((x, 62), 'Shar', font=_fuente(38), fill=BLANCO)
    d.text((x + d.textlength('Shar', font=_fuente(38)), 62), 'Picks', font=_fuente(38), fill=VERDE)
    d.text((x, 108), _corta(d, titulo.upper(), _fuente(24), 560), font=_fuente(24), fill=TENUE)
    fe = _fuente(30)
    ew = d.textlength(etiqueta, font=fe) + 44
    d.rounded_rectangle([ANCHO - 70 - ew, 66, ANCHO - 70, 120], radius=27, fill=ORO)
    d.text((ANCHO - 70 - ew + 22, 74), etiqueta, font=fe, fill=FONDO)
    # el grito
    d.rounded_rectangle([70, 158, ANCHO - 70, 296], radius=28, fill=VERDE)
    tg, fg = '¡GANAMOS!', _fuente(92)
    d.text(((ANCHO - d.textlength(tg, font=fg)) / 2, 172), tg, font=fg, fill=FONDO)
    y = cab_h
    for p in patas:
        # palomita dibujada: la fuente no trae emoji
        d.ellipse([70, y + 10, 124, y + 64], fill=VERDE)
        d.line([(84, y + 38), (94, y + 49), (111, y + 25)], fill=FONDO, width=7)
        d.text((144, y + 6), _corta(d, p.get('apuesta', ''), _fuente(36), ANCHO - 220), font=_fuente(36), fill=BLANCO)
        sub = str(p.get('partido', '')) + ('  ' + str(p.get('marcador')) if p.get('marcador') else '')
        d.text((144, y + 56), _corta(d, sub, _fuente(26, False), ANCHO - 220), font=_fuente(26, False), fill=TENUE)
        y += fila_h
    d.line([(70, y), (ANCHO - 70, y)], fill=BORDE, width=2)
    d.text((70, y + 20), 'Cuota', font=_fuente(28, False), fill=TENUE)
    d.text((70, y + 54), ap + '%.2f' % cuota_total, font=_fuente(56), fill=VERDE)
    tx = 'Apostando %s' % _pesos(apuesta)
    d.text((ANCHO - 70 - d.textlength(tx, font=_fuente(30, False)), y + 26), tx, font=_fuente(30, False), fill=TENUE)
    tc = 'cobras %s%s' % (ap, _pesos(apuesta * cuota_total))
    d.text((ANCHO - 70 - d.textlength(tc, font=_fuente(40)), y + 62), tc, font=_fuente(40), fill=BLANCO)
    tg2, fg2 = '%s+%s de ganancia' % (ap, _pesos(apuesta * (cuota_total - 1))), _fuente(60)
    d.rounded_rectangle([70, y + 132, ANCHO - 70, y + 228], radius=24, fill=ORO)
    d.text(((ANCHO - d.textlength(tg2, font=fg2)) / 2, y + 146), tg2, font=fg2, fill=FONDO)
    d.text((70, alto - 78), 'sharpicksapp.com  ·  +18  ·  juega con responsabilidad', font=_fuente(24, False), fill=TENUE)
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


def invita_vip(titulo: str, patas: List[Dict], apuesta: int, cuota_total: float, numeros: Optional[Dict] = None, aprox: bool = False) -> bytes:
    """v579 — EL USUARIO: «en el gratis, que si se hubieran unido al VIP hubieran tenido ese parley; atraer a que se unan». Lo que cobró el VIP, contado desde
    afuera: no dice «¡ganamos!» porque en este canal no se mandó. Lleva los números reales de la semana, verdes Y rojos: eso es lo que da confianza."""
    ap = '~' if aprox else ''
    patas = patas[:6]
    fila_h, cab_h = 118, 330
    alto = cab_h + fila_h * len(patas) + 448 + (70 if numeros else 0)
    im = Image.new('RGB', (ANCHO, alto), (20, 14, 44))
    d = ImageDraw.Draw(im)
    for i in range(alto):                       # fondo morado, el color del VIP, que se apaga hacia abajo
        t = i / alto
        d.line([(0, i), (ANCHO, i)], fill=(int(58 - 38 * t), int(34 - 20 * t), int(112 - 68 * t)))
    d.rounded_rectangle([30, 30, ANCHO - 30, alto - 30], radius=36, fill=(15, 18, 38), outline=ORO, width=6)
    x = 70
    try:
        logo = Image.open(os.path.join(AQUI, 'web', 'marca', 'logo-96.png')).convert('RGBA').resize((76, 76))
        im.paste(logo, (x, 58), logo)
        x += 94
    except Exception:
        pass
    d.text((x, 62), 'Shar', font=_fuente(38), fill=BLANCO)
    d.text((x + d.textlength('Shar', font=_fuente(38)), 62), 'Picks', font=_fuente(38), fill=VERDE)
    d.text((x, 108), _corta(d, titulo.upper(), _fuente(24), 500), font=_fuente(24), fill=TENUE)
    fe, et = _fuente(30), 'SÓLO VIP'
    ew = d.textlength(et, font=fe) + 44
    d.rounded_rectangle([ANCHO - 70 - ew, 66, ANCHO - 70, 120], radius=27, fill=ORO)
    d.text((ANCHO - 70 - ew + 22, 74), et, font=fe, fill=FONDO)
    d.rounded_rectangle([70, 158, ANCHO - 70, 296], radius=28, fill=ORO)
    tg, fg = 'LOS VIP COBRARON', _fuente(78)
    d.text(((ANCHO - d.textlength(tg, font=fg)) / 2, 184), tg, font=fg, fill=FONDO)
    y = cab_h
    for p in patas:
        d.ellipse([70, y + 10, 124, y + 64], fill=VERDE)
        d.line([(84, y + 38), (94, y + 49), (111, y + 25)], fill=FONDO, width=7)
        d.text((144, y + 6), _corta(d, p.get('apuesta', ''), _fuente(36), ANCHO - 220), font=_fuente(36), fill=BLANCO)
        sub = str(p.get('partido', '')) + ('  ' + str(p.get('marcador')) if p.get('marcador') else '')
        d.text((144, y + 56), _corta(d, sub, _fuente(26, False), ANCHO - 220), font=_fuente(26, False), fill=TENUE)
        y += fila_h
    d.line([(70, y), (ANCHO - 70, y)], fill=BORDE, width=2)
    d.text((70, y + 20), 'Cuota', font=_fuente(28, False), fill=TENUE)
    d.text((70, y + 54), ap + '%.2f' % cuota_total, font=_fuente(56), fill=ORO)
    tx = 'Con %s' % _pesos(apuesta)
    d.text((ANCHO - 70 - d.textlength(tx, font=_fuente(30, False)), y + 26), tx, font=_fuente(30, False), fill=TENUE)
    tc = '%s+%s de ganancia' % (ap, _pesos(apuesta * (cuota_total - 1)))
    d.text((ANCHO - 70 - d.textlength(tc, font=_fuente(44)), y + 62), tc, font=_fuente(44), fill=BLANCO)
    y += 136
    if numeros:
        tn = 'VIP, últimos 7 días:  %d verdes  ·  %d rojas  ·  %d %%' % (numeros['v'], numeros['r'], round(100 * numeros['v'] / max(1, numeros['v'] + numeros['r'])))
        fn = _fuente(30)
        d.text(((ANCHO - d.textlength(tn, font=fn)) / 2, y + 6), tn, font=fn, fill=BLANCO)
        y += 70
    d.rounded_rectangle([70, y, ANCHO - 70, y + 150], radius=26, fill=VERDE)
    t1, f1 = 'ÚNETE AL VIP', _fuente(68)
    d.text(((ANCHO - d.textlength(t1, font=f1)) / 2, y + 14), t1, font=f1, fill=FONDO)
    t2, f2 = 'recibe el próximo antes del partido', _fuente(30, False)
    d.text(((ANCHO - d.textlength(t2, font=f2)) / 2, y + 100), t2, font=f2, fill=FONDO)
    d.text((70, alto - 112), 'Lo que ya pasó no asegura lo que viene.', font=_fuente(24, False), fill=TENUE)
    d.text((70, alto - 78), 'sharpicksapp.com  ·  +18  ·  juega con responsabilidad', font=_fuente(24, False), fill=TENUE)
    b = io.BytesIO()
    im.save(b, 'PNG', optimize=True)
    return b.getvalue()
