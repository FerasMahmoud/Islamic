const CACHE_NAME = 'islamic-v10';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  'https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400;1,700&family=Scheherazade+New:wght@400;500;600;700&family=Noto+Naskh+Arabic:wght@400;500;600;700&display=swap'
];

// Install: cache all core assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: cache-first, fallback to network, then cache the response
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Cache fonts, page, and Quran API responses for offline use
        if (response.ok && (
          event.request.url.includes('fonts.g') ||
          event.request.url.includes('index.html') ||
          event.request.url.endsWith('/') ||
          event.request.url.includes('api.alquran.cloud') ||
          event.request.url.includes('api.aladhan.com') ||
          event.request.url.includes('cdn.jsdelivr.net/gh/spa5k/tafsir_api')
        )) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    }).catch(() => {
      // If offline and not cached, return the cached index
      return caches.match('./index.html');
    })
  );
});
