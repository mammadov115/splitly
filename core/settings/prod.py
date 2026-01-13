from .base import *
import os

DEBUG = False

# PythonAnywhere domenini əlavə edirik
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "xercler.pythonanywhere.com").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "xercler$splitly_db"), # User$DB_adı formatında
        "USER": os.getenv("DB_USER", "xercler"),
        "PASSWORD": os.getenv("DB_PASSWORD"), # .env faylındakı MySQL şifrən
        "HOST": os.getenv("DB_HOST", "xercler.mysql.pythonanywhere-services.com"),
        "PORT": os.getenv("DB_PORT", "3306"), # MySQL üçün port 3306-dır
    }
}

# PythonAnywhere pulsuz planında SSL redirect bəzən problem yarada bilər, 
# çünki onlar özləri SSL-i idarə edir. Ehtiyat üçün bunları saxlayaq:
SECURE_SSL_REDIRECT = False # Əgər sayt açılmasa bunu True et
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Statik və Media fayllar üçün mütləq yollar
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")