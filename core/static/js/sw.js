/* Service Worker — обрабатывает push-уведомления */
self.addEventListener('push', function(event) {
    let data = {};
    try { data = event.data.json(); } catch(e) {}

    const title = data.title || 'Charity AlmaU';
    const options = {
        body: data.body || 'Новое сообщение',
        icon: '/static/logo.png',
        badge: '/static/logo.png',
        data: { url: data.url || '/chat/' },
        vibrate: [200, 100, 200],
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const url = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : '/chat/';
    event.waitUntil(clients.openWindow(url));
});
