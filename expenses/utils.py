from firebase_admin.messaging import Message, Notification, WebpushConfig, WebpushNotification
import datetime
import os
from fcm_django.models import FCMDevice


def log(message):
    # Faylın tam yolunu təyin edirik (PythonAnywhere-dəki yolun)
    log_path = os.path.join(os.path.expanduser("~"), "my_debug.txt")
    with open(log_path, "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")




def send_live_notification(user, title, body):
    devices = FCMDevice.objects.filter(user=user, active=True)
    
    if devices.exists():
        try:
            # Bildirişi WebpushNotification klası ilə yaradırıq
            web_notification = WebpushNotification(
                title=title,
                body=body,
                icon="/static/images/logo.png" # Opsionaldır
            )

            webpush = WebpushConfig(
                notification=web_notification
            )

            devices.send_message(
                Message(
                    notification=Notification(title=title, body=body),
                    webpush=webpush
                )
            )
            log(f"Firebase UGURLU: Mesaj {user.username} ucun gonderildi.")
        except Exception as e:
            log(f"Firebase Göndərmə Xətası: {str(e)}")
