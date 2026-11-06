// SharPicks Service Worker — caché acotada y segura.
// Sólo almacena recursos estáticos del mismo origen. Nunca cachea respuestas API,
// páginas HTML, rutas dinámicas ni URLs con query string (datos en vivo).
const CACHE = 'sharpicks-static-v2';
const VIEJO = self.location.hostname === 'sharpicks.pages.dev';

const ASSET_EXTENSIONS = new Set([
  '.css', '.js', '.mjs', '.png', '.jpg', '.jpeg', '.webp', '.gif',
  '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf'
]);

function esRecursoEstatico(request, url) {
  if (VIEJO || request.method !== 'GET' || url.origin !== self.location.origin) return false;
  if (url.search || url.hash) return false;
  if (request.headers.has('authorization')) return false;
  if (url.pathname.startsWith('/rest/') || url.pathname.startsWith('/functions/')) return false;
  if (url.pathname.startsWith('/vivo') || url.pathname.startsWith('/presion')) return false;
  const extension = url.pathname.slice(url.pathname.lastIndexOf('.')).toLowerCase();
  return ASSET_EXTENSIONS.has(extension);
}

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    if (VIEJO) {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
      await self.registration.unregister();
      const clients = await self.clients.matchAll({ type: 'window' });
      clients.forEach((client) => client.navigate(client.url));
      return;
    }

    // Conserva únicamente la versión vigente; evita acumulación indefinida.
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (!esRecursoEstatico(request, url)) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fetch(request);
      if (response && response.ok && response.type === 'basic') {
        await cache.put(request, response.clone());
      }
      return response;
    } catch (error) {
      const cached = await cache.match(request);
      if (cached) return cached;
      throw error;
    }
  })());
});
