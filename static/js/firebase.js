// 1. Konfiqurasiya
const firebaseConfig = {
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
};

// Yalnız bir dəfə başlatmaq üçün yoxlama
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const messaging = firebase.messaging();
const VAPID_KEY = "BMte8ksgtT1hD0rwFrz3Z6GNsdgpAbwUZqMazMhd-LSKoQwcVSJhm3oz4cLTohbcyCKqzCg2h1P8QczshD7D7Ik";

// 2. Tokeni Serverə Göndərmə Funksiyası
function sendTokenToServer(token) {
    fetch('/register-device/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ token: token, type: 'web' })
    })
    .then(response => response.json())
    .then(data => console.log("Cihaz statusu serverdə yeniləndi:", data))
    .catch(err => console.error("Serverlə əlaqə xətası:", err));
}

// 3. Bildiriş İcazəsi və Token Alınması
function requestPermissionAndGetToken() {
    console.log('Bildiriş icazəsi tələb olunur...');
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('İcazə verildi. Token alınır...');
            messaging.getToken({ vapidKey: VAPID_KEY })
                .then((currentToken) => {
                    if (currentToken) {
                        console.log('FCM Token alındı:', currentToken);
                        sendTokenToServer(currentToken);
                    } else {
                        console.warn('Token alınmadı. Brauzer icazələrini yoxlayın.');
                    }
                })
                .catch((err) => {
                    console.error('Token alma zamanı xəta:', err);
                });
        } else {
            console.warn('İstifadəçi bildiriş icazəsini rədd etdi.');
        }
    });
}

// 4. Service Worker Qeydiyyatı və İşə Salınma
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/firebase-messaging-sw.js')
        .then((registration) => {
            console.log('Service Worker qeydiyyatı uğurlu:', registration.scope);
            
            // Yenilənməni yoxla
            registration.onupdatefound = () => {
                const installingWorker = registration.installing;
                installingWorker.onstatechange = () => {
                    if (installingWorker.state === 'installed') {
                        if (navigator.serviceWorker.controller) {
                            console.log('Yeni versiya mövcuddur, tətbiq yenilənir...');
                        }
                    }
                };
            };

            requestPermissionAndGetToken();
        }).catch((err) => {
            console.error('Service Worker qeydiyyat xətası:', err);
        });
    });

    // SW aktivləşən kimi səhifəni 1 dəfə yenilə (isteğe bağlı)
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
            window.location.reload();
            refreshing = true;
        }
    });
}

// Django üçün CSRF Token funksiyası
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}