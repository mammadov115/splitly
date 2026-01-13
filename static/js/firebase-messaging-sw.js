// // firebase-messaging-sw.js
// importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js');
// importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-messaging-compat.js');

// firebase.initializeApp({
//     apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
//     projectId: "expenses-74419",
//     messagingSenderId: "1018709351789",
//     appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
// });

// const messaging = firebase.messaging();


// // Arxa fonda mesaj gələndə onu tutub ekranda göstərmək üçün:
// messaging.onBackgroundMessage((payload) => {
//     console.log('Mesaj gəldi (Background): ', payload);

//     const notificationTitle = payload.notification.title;
//     const notificationOptions = {
//         body: payload.notification.body,
//         // icon: '/static/images/logo.png', // Saytının loqosunun yolu (vacib deyil, amma yaxşı olar)
//         data: { url: '/' } // Bildirişə basanda hara getsin
//     };

//     self.registration.showNotification(notificationTitle, notificationOptions);
// });


importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('[sw.js] Mesaj alındı: ', payload);

    // Bildirişə klikləyəndə saytı açmaq üçün
    self.addEventListener('notificationclick', (event) => {
        event.notification.close();
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/')
        );
    });

    // Əgər notification obyekti yoxdursa, data-dan oxumağa çalışırıq
    const title = (payload.notification && payload.notification.title) || 
                  (payload.data && payload.data.title) || 
                  "Yeni Bildiriş";

    const body = (payload.notification && payload.notification.body) || 
                 (payload.data && payload.data.body) || 
                 "Məzmun yoxdur";

    const notificationOptions = {
        body: body,
        // icon: '/static/images/logo.png',
        data: { url: (payload.data && payload.data.url) || '/' },
        vibrate: [200, 100, 200] // Telefonlar üçün vibrasiya
    };

    // Bildirişi ekrana çıxarırıq
    return self.registration.showNotification(title, notificationOptions);
});