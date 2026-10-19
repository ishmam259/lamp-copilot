// LaMP service worker: shows desktop notifications for `notify` events and opens the
// linked screen on click. A notification never approves anything; it only opens the app.
// Click handling follows MDN's notificationclick example.

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.link || "/", self.location.origin).href;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      const open = clients.find((c) => new URL(c.url).origin === self.location.origin);
      if (open) return open.focus().then((c) => (c && "navigate" in c ? c.navigate(target) : c));
      return self.clients.openWindow(target);
    })
  );
});
