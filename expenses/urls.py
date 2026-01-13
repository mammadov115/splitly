from django.urls import path
from . import views
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('api/add-expense/', views.add_expense_ajax, name='add_expense'),  # Yeni xərc əlavə etmək üçün API endpoint
    # AJAX üçün settle request URL-i
    path('settle-request/<int:split_id>/', views.settle_request_view, name='settle_request'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('api/approve-split/<int:split_id>/', views.approve_split, name='approve_split'),
    path('balance/', views.BalanceView.as_view(), name='balance'),
    path('api/register-device/', views.register_device, name='register_device'),
    
]