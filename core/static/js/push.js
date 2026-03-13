/* Регистрация push-подписки */
(function () {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
    if (!window.VAPID_PUBLIC_KEY) return;

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const raw = window.atob(base64);
        return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
    }

    async function subscribe() {
        try {
            const reg = await navigator.serviceWorker.register('/static/js/sw.js');
            await navigator.serviceWorker.ready;

            const permission = await Notification.requestPermission();
            if (permission !== 'granted') return;

            const existing = await reg.pushManager.getSubscription();
            if (existing) {
                sendToServer(existing, '/chat/push/subscribe/');
                return;
            }

            const sub = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(window.VAPID_PUBLIC_KEY),
            });
            sendToServer(sub, '/chat/push/subscribe/');
        } catch (e) {
            console.warn('Push subscribe error:', e);
        }
    }

    function sendToServer(sub, url) {
        const data = sub.toJSON();
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(data),
        });
    }

    function getCookie(name) {
        const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
        return v ? v[2] : '';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', subscribe);
    } else {
        subscribe();
    }
})();
