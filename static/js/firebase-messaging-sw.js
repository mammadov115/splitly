// firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
});

const messaging = firebase.messaging();


// Arxa fonda mesaj gələndə onu tutub ekranda göstərmək üçün:
messaging.onBackgroundMessage((payload) => {
    console.log('Mesaj gəldi (Background): ', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        // icon: '/static/images/logo.png', // Saytının loqosunun yolu (vacib deyil, amma yaxşı olar)
        data: { url: '/' } // Bildirişə basanda hara getsin
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});