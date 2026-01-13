// firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-sw.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-sw.js');

firebase.initializeApp({
    apiKey: "AIzaSyBlKHXjRdd47mUFx7E0Vd_jlvzbHFobHYc",
    projectId: "expenses-74419",
    messagingSenderId: "1018709351789",
    appId: "1:1018709351789:web:3a0cfaedccfea91f598e64"
});

const messaging = firebase.messaging();