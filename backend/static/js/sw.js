/* RB Prospecta - Service Worker (TRD §6)
   - Estáticos (CSS/JS/ícones): cache-first
   - Navegação/dados: network-first com fallback offline */
const CACHE = "rb-prospecta-v1";
const ESTATICOS = [
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/manifest.json",
  "/static/icon-192.png",
  "/static/icon-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ESTATICOS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((chaves) =>
        Promise.all(chaves.filter((c) => c !== CACHE).map((c) => caches.delete(c)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);

  // Só GET do mesmo origin
  if (evento.request.method !== "GET" || url.origin !== self.location.origin) return;

  // Estáticos: cache primeiro
  if (url.pathname.startsWith("/static/")) {
    evento.respondWith(
      caches.match(evento.request).then((cacheado) => cacheado || fetch(evento.request))
    );
    return;
  }

  // Navegação e dados: rede primeiro, fallback para cache
  evento.respondWith(
    fetch(evento.request)
      .then((resposta) => {
        const copia = resposta.clone();
        if (resposta.ok && url.pathname !== "/contas/entrar/") {
          caches.open(CACHE).then((cache) => cache.put(evento.request, copia));
        }
        return resposta;
      })
      .catch(() => caches.match(evento.request))
  );
});
