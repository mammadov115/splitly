import os
import datetime
from django.conf import settings
import firebase_admin
from firebase_admin import credentials
from fcm_django.models import FCMDevice


def log(message):
    log_path = os.path.join(settings.BASE_DIR, 'my_debug.txt')
    with open(log_path, "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

def initialize_firebase():
    """Firebase-i yalnız bir dəfə və lazım olduqda başladır."""
    if not firebase_admin._apps:
        try:
            cert_path = getattr(settings, 'FIREBASE_CERT_PATH', None)
            if cert_path and os.path.exists(cert_path):
                cred = credentials.Certificate(cert_path)
                firebase_admin.initialize_app(cred)
                log("Firebase lazy initialization successful.")
            else:
                log("Firebase certificate file not found.")
        except Exception as e:
            log(f"Firebase initialization error: {e}")




def send_live_notification(user, title, body):
    initialize_firebase()
    from firebase_admin.messaging import Message
    devices = FCMDevice.objects.filter(user=user, active=True)
    if devices.exists():
        try:
            # Həm notification, həm də data olaraq göndəririk
            message = Message(
                data={ # Notification yox, məhz DATA istifadə edirik ki, SW mütləq işə düşsün
                    'title': title,
                    'body': body,
                },
                token=devices.first().registration_id,  # Yalnız bir cihaz üçün nümunə
            )

            devices.send_message(message)
            log(f"Firebase UGURLU: {user.username} ucun gonderildi.")
        except Exception as e:
            log(f"Firebase Xetasi: {str(e)}")