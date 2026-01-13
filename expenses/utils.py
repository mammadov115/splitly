from firebase_admin.messaging import Message, Notification, WebpushConfig, WebpushNotificationAction
import datetime
import os


def log(message):
    # Faylın tam yolunu təyin edirik (PythonAnywhere-dəki yolun)
    log_path = os.path.join(os.path.expanduser("~"), "my_debug.txt")
    with open(log_path, "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")



def send_live_notification(user, title, body):
    log(f"Sending live notification to {user.username}: {title} - {body}")
    devices = FCMDevice.objects.filter(user=user, active=True)
    log(f"Found {devices.count()} active devices for user {user.username}")
    
    if devices.exists():
        # Webpush üçün xüsusi nizamlamalar
        log(f"Setting up WebpushConfig for user {user.username}")
        webpush = WebpushConfig(
            notification={
                "title": title,
                "body": body,
                "icon": "/static/images/logo.png", # Bura öz loqonun yolunu yaz
                "vibrate": [200, 100, 200],
                "requireInteraction": True, # İstifadəçi bağlamayana qədər ekranda qalsın
            }
        )
        log(f"WebpushConfig set up: {webpush}")
        try:
            response = devices.send_message(
                Message(
                    notification=Notification(
                        title=title,
                        body=body
                    ),
                    webpush=webpush # Web nizamlamasını əlavə etdik
                )
            )
            log(f"Firebase Response: {response}")
        except Exception as e:
            log(f"Firebase Göndərmə Xətası: {str(e)}")
    else:
        log(f"No active devices found for user {user.username}")


