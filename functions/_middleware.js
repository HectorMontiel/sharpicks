// v512 — EL SITIO SE MUDÓ A sharpicksapp.com.
// El usuario: «todos los que ya tenían instalada la app con el anterior dominio, ¿cómo los redirigen?».
// En sharpicks.pages.dev:
//   · la navegación (una página HTML) recibe una página mínima con /mudanza.js: ese script lleva la sesión
//     y las preferencias del navegador (localStorage, que es de cada dominio) al nuevo, en el fragmento #,
//     que nunca llega a ningún servidor. Un 301 directo los dejaría sin sesión.
//   · sw.js y mudanza.js se sirven tal cual: el service worker viejo tiene que poder actualizarse (un
//     redirect en sw.js lo dejaría pegado sirviendo la versión vieja guardada).
//   · todo lo demás (archivos, datos, /presion, /vivo): 301 al mismo camino en el dominio nuevo.
// Los despliegues de prueba (<hash>.sharpicks.pages.dev) no se tocan.
const VIEJO = 'sharpicks.pages.dev';
const NUEVO = 'https://sharpicksapp.com';
const PAGINA = '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width,initial-scale=1"><title>SharPicks se mudó</title>' +
  '<script src="/mudanza.js"></script></head>' +
  '<body style="background:#0b1220;color:#e5e7eb;font-family:system-ui,sans-serif;text-align:center;padding:48px 16px">' +
  '<p>SharPicks ahora está en <a style="color:#4ade80" href="' + NUEVO + '/">sharpicksapp.com</a>.</p>' +
  '<p style="opacity:.7">Te llevamos en un momento…</p></body></html>';

export async function onRequest(ctx) {
  const u = new URL(ctx.request.url);
  if (u.hostname !== VIEJO) return ctx.next();
  if (u.pathname === '/sw.js' || u.pathname === '/mudanza.js') return ctx.next();
  const acepta = ctx.request.headers.get('accept') || '';
  if (ctx.request.method === 'GET' && acepta.includes('text/html')) {
    return new Response(PAGINA, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });
  }
  return Response.redirect(NUEVO + u.pathname + u.search, 301);
}
