from firebase_admin.messaging import Message, Notification, WebpushConfig, WebpushNotificationAction

def send_live_notification(user, title, body):
    print(f"Sending live notification to {user.username}: {title} - {body}")
    devices = FCMDevice.objects.filter(user=user, active=True)
    print(f"Found {devices.count()} active devices for user {user.username}")
    
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

            print(f"Firebase Cavabı: {response}")
        except Exception as e:
            print(f"Firebase Göndərmə Xətası: {str(e)}")
    else:
        print(f"No active devices found for user {user.username}")


def log(message):
    # Faylın tam yolunu təyin edirik (PythonAnywhere-dəki yolun)
    log_path = os.path.join(os.path.expanduser("~"), "my_debug.txt")
    with open(log_path, "a") as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")