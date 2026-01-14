"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
import os
from core import settings
from django.views.generic import TemplateView
from django.http import HttpResponse


# Service Worker faylını oxuyub qaytaran balaca bir funksiya
def service_worker(request):
    # Faylın tam yolunu tapırıq (manage.py olan qovluqda)
    sw_path = os.path.join(settings.base.BASE_DIR, 'firebase-messaging-sw.js')
    with open(sw_path, 'rb') as f:
        return HttpResponse(f.read(), content_type="application/javascript")

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('firebase-messaging-sw.js', serve, {
    #     'document_root': os.path.join(settings.base.BASE_DIR, 'static/js'),
    #     'path': 'firebase-messaging-sw.js'
    # }),
    path('firebase-messaging-sw.js', service_worker),
    path("", include("expenses.urls")),
    
    
]
