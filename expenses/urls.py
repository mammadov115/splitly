from django.urls import path
from .views import UserLoginView, UserRegisterView, UserLogoutView, HomeView, add_expense_ajax

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('api/add-expense/', add_expense_ajax, name='add_expense'),  # Yeni xərc əlavə etmək üçün API endpoint
]