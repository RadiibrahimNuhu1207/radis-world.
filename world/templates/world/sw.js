{% load static %}/* Radi's World service worker: offline app shell + daily push notifications. */
const CACHE = "radi-v1";
const SHELL = ["/", {% for s in shell %}"{{ s }}", {% endfor %}];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith("/admin") || url.pathname.startsWith("/api/")) return;
  if (url.pathname.startsWith("/media/")) return;          // videos stream from the network
  if (req.mode === "navigate") {                                   // fresh page when online, saved copy when offline
    event.respondWith(
      fetch(req).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put("/", copy)); return res; })
        .catch(() => caches.match("/"))
    );
    return;
  }
  if (url.pathname.endsWith(".js") || url.pathname.endsWith(".css")) {   // code: fresh when online
    event.respondWith(
      fetch(req).then(res => { if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); } return res; })
        .catch(() => caches.match(req))
    );
    return;
  }
  event.respondWith(                                               // posters, sounds, icons: cache first
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }))
  );
});

self.addEventListener("push", event => {
  let d = {};
  try { d = event.data.json(); } catch (e) { d = { body: event.data ? event.data.text() : "" }; }
  event.waitUntil(self.registration.showNotification(d.title || "Radi's World", {
    body: d.body || "",
    icon: d.icon || "{% static 'world/icons/icon-192.png' %}",
    badge: "{% static 'world/icons/icon-192.png' %}",
    image: d.image || undefined,
    tag: "radi-daily",
    data: { url: d.url || "/" }
  }));
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(clients.matchAll({ type: "window", includeUncontrolled: true }).then(wins => {
    for (const w of wins) { if ("focus" in w) { w.navigate(url); return w.focus(); } }
    return clients.openWindow(url);
  }));
});
