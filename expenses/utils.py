from firebase_admin.messaging import Message, Notification, WebpushConfig, WebpushNotification
import datetime
import os
from fcm_django.models import FCMDevice
from django.conf import settings


def log(message):
    # Faylın tam yolunu təyin edirik (PythonAnywhere-dəki yolun)
    log_path = os.path.join(settings.BASE_DIR, 'my_debug.txt')
    with open(log_path, "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")




def send_live_notification(user, title, body):
    devices = FCMDevice.objects.filter(user=user, active=True)
    if devices.exists():
        try:
            # Həm notification, həm də data olaraq göndəririk
            message = Message(
                notification=Notification(title=title, body=body),
                data={
                    "title": title,
                    "body": body,
                    "url": "/expenses/", # Klikləyəndə bura getsin
                },
                webpush=WebpushConfig(
                    notification=WebpushNotification(
                        title=title,
                        body=body,
                        icon="/static/logo.png"
                    )
                )
            )
            devices.send_message(message)
            log(f"Firebase UGURLU: {user.username} ucun gonderildi.")
        except Exception as e:
            log(f"Firebase Xetasi: {str(e)}")