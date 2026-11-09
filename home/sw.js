// ES: Service worker de LabTower: solo muestra «Sin conexión» cuando el servidor no responde a una página. Guarda únicamente esa página y sus
//     archivos (nunca datos de los módulos) y no toca ninguna otra solicitud. Cambiar VERSION reemplaza lo guardado.
// EN: LabTower service worker: it only shows "No connection" when the server does not answer a page. It stores only that page and its files
//     (never module data) and leaves every other request alone. Changing VERSION replaces what is stored.
const VERSION = "1";
const CACHE = "labtower-offline-" + VERSION;
const FILES = ["/offline.html", "/offline.css", "/offline.js", "/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k.startsWith("labtower-offline-") && k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // Páginas: siempre a la red; solo si no hay respuesta, la página guardada. / EN: Pages: always the network; only without an answer, the stored page.
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).catch(() => caches.match("/offline.html")));
    return;
  }
  // Los archivos de la página «Sin conexión», desde lo guardado. / EN: The "No connection" page files, from the store.
  if (FILES.includes(url.pathname)) e.respondWith(caches.match(url.pathname).then((r) => r || fetch(req)));
});
