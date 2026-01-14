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
                data={ # Notification yox, məhz DATA istifadə edirik ki, SW mütləq işə düşsün
                    'title': 'Xərc əlavə edildi',
                    'body': 'Məbləğ: 50 AZN',
                },
                token=devices.first().registration_id,  # Yalnız bir cihaz üçün nümunə
            )

            devices.send_message(message)
            log(f"Firebase UGURLU: {user.username} ucun gonderildi.")
        except Exception as e:
            log(f"Firebase Xetasi: {str(e)}")