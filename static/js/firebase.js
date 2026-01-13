// Firebase-i tətbiq daxilində başladırıq (sw faylındakı ilə eyni konfiqurasiya)
const firebaseConfig = {
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// VAPID Key-i Firebase Console-dan bura yapışdır
const VAPID_KEY = "BMte8ksgtT1hD0rwFrz3Z6GNsdgpAbwUZqMazMhd-LSKoQwcVSJhm3oz4cLTohbcyCKqzCg2h1P8QczshD7D7Ik";

// 1. İcazə istəyirik
Notification.requestPermission().then((permission) => {
    if (permission === 'granted') {
        // 2. Tokeni alırıq
        messaging.getToken({ vapidKey: VAPID_KEY }).then((currentToken) => {
            if (currentToken) {
                // 3. Tokeni Django bazasına göndəririk
                sendTokenToServer(currentToken);
            }
        });
    }
});

let isTokenSent = false;
function sendTokenToServer(token) {
    if (isTokenSent) return;
    fetch('/register-device/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Django CSRF təhlükəsizliyi
        },
        body: JSON.stringify({ token: token, type: 'web' })
    })
    .then(response => response.json())
    .then(data => console.log("Cihaz qeydiyyatı:", data));
    isTokenSent = true;
}

// CSRF Tokeni götürmək üçün köməkçi funksiya
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

// Xidmət işçisini qeydiyyatdan keçiririk
// if ('serviceWorker' in navigator) {
//     navigator.serviceWorker.register('/static/js/firebase-messaging-sw.js')
//     .then(function(registration) {
//         console.log('Registration successful, scope is:', registration.scope);
//     }).catch(function(err) {
//         console.log('Service worker registration failed, error:', err);
//     });
// }

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then(function(registration) {
        console.log('Registration successful, scope is:', registration.scope);

        // Service Worker-in tam aktiv olmasını gözləyirik
        return navigator.serviceWorker.ready; 
    })
    .then(function(activeRegistration) {
        // İndi Service Worker aktivdir, token istəyə bilərik
        console.log('Service Worker artıq aktivdir.');
        
        messaging.getToken({ 
            vapidKey: VAPID_KEY,
            serviceWorkerRegistration: activeRegistration // Aktiv registration-u bura ötürürük
        })
        .then((currentToken) => {
            if (currentToken) {
                sendTokenToServer(currentToken);
            }
        })
        .catch((err) => {
            console.log('Token alınarkən xəta:', err);
        });
    })
    .catch(function(err) {
        console.log('Service worker registration failed:', err);
    });
}

