from firebase_admin.messaging import Message, Notification, WebpushConfig, WebpushNotificationAction

def send_live_notification(user, title, body):
    devices = FCMDevice.objects.filter(user=user, active=True)
    
    if devices.exists():
        # Webpush üçün xüsusi nizamlamalar
        webpush = WebpushConfig(
            notification={
                "title": title,
                "body": body,
                "icon": "/static/images/logo.png", # Bura öz loqonun yolunu yaz
                "vibrate": [200, 100, 200],
                "requireInteraction": True, # İstifadəçi bağlamayana qədər ekranda qalsın
            }
        )

        devices.send_message(
            Message(
                notification=Notification(
                    title=title,
                    body=body
                ),
                webpush=webpush # Web nizamlamasını əlavə etdik
            )
        )