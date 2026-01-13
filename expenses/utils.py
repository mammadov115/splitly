from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification as FirebaseNotification

def send_live_notification(user, title, body):
    # İstifadəçinin bütün aktiv cihazlarını tapırıq
    devices = FCMDevice.objects.filter(user=user, active=True)
    
# Əgər istifadəçinin qeydiyyatlı cihazı varsa göndər
    if devices.exists():
        devices.send_message(
            Message(
                notification=FirebaseNotification(
                    title=title,
                    body=body
                ),
                # Əlavə məlumat göndərmək üçün (məs: klikləyəndə xərcə getsin)
                data={
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    "type": "new_expense",
                }
            )
        )