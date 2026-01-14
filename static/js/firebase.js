// 1. Konfiqurasiya
const firebaseConfig = {
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
};

firebase.initializeApp(firebaseConfig);
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
    .then(data => console.log("Cihaz statusu yeniləndi:", data))
    .catch(err => console.error("Serverlə əlaqə xətası:", err));
}

// 3. Əsas Aktivləşdirmə Məntiqi
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js') // Sonda / YOXDUR
    .then((registration) => {
        console.log('SW Qeydiyyatı OK:', registration.scope);
    }).catch((err) => {
        console.error('SW Qeydiyyat xətası:', err);
    });
}

// CSRF Funksiyası
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