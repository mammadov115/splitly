importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
});

const messaging = firebase.messaging();

// Mesaj gələndə sadəcə bu işləyəcək
messaging.onBackgroundMessage((payload) => {
    console.log("SW: Mesaj tutuldu!", payload);

    const title = payload.data?.title || "Test Başlıq";
    const body = payload.data?.body || "Test Məzmun";

    return self.registration.showNotification(title, {
        body: body,
        icon: 'https://via.placeholder.com/128' // Test üçün müvəqqəti ikon
    });
});