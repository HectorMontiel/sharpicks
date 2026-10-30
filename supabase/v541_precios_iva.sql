-- v541 — PRECIOS CON IVA Y COMISIÓN. El usuario (30-oct): «en México hay comisiones, por eso tenemos que tomar en
-- cuenta el IVA… si se tiene que corregir, corrígelos ya». Antes el precio de la página ERA lo cobrado: de $149 salían
-- el IVA (16 %) y la comisión de Stripe (3,6 % + $3, más IVA) y quedaban ~$119. Ahora cada precio deja limpio, como
-- mínimo, lo que antes era el precio: precio = (limpio + 3,48) / (1/1,16 − 0,036·1,16), redondeado hacia arriba a 9.
--   VIP mensual 149 → 189 · fundador 99 → 129 · semestral 749 → 919
--   monedas: 50 = 29 → 39 · 100 = 49 → 65 · 220 = 99 → 129 · 500 = 199 → 249
-- Las suscripciones que ya existen siguen con su precio (Stripe y Mercado Pago lo guardan al suscribirse).

update public.ajustes set valor = '189' where clave = 'precio_mensual';
update public.ajustes set valor = '129' where clave = 'precio_fundador';
update public.ajustes set valor = '919' where clave = 'precio_semestral';

update public.paquetes set precio = 39 where id = 'prueba';
update public.paquetes set precio = 65 where id = 'popular';
update public.paquetes set precio = 129 where id = 'pro';
update public.paquetes set precio = 249 where id = 'mega';
