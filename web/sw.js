// v378 — Para que se pueda instalar como app en el celular. Siempre pide a la
// red primero (los datos cambian a cada rato); sin red, lo último guardado.
const CACHE = 'sharpicks-v1';
// v512 — en el dominio viejo (sharpicks.pages.dev) el service worker se borra solo con lo guardado: así
// la siguiente visita llega a la red, donde la página de mudanza lleva al usuario a sharpicksapp.com.
const VIEJO = self.location.hostname === 'sharpicks.pages.dev';
self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(VIEJO
  ? caches.keys().then((ks) => Promise.all(ks.map((k) => caches.delete(k))))
    .then(() => self.registration.unregister())
    .then(() => self.clients.matchAll({ type: 'window' }))
    .then((cs) => cs.forEach((c) => c.navigate(c.url)))
  : self.clients.claim()));
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (VIEJO || e.request.method !== 'GET' || u.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then((r) => {
    const c = r.clone(); caches.open(CACHE).then((k) => k.put(e.request, c)); return r;
  }).catch(() => caches.match(e.request)));
});
