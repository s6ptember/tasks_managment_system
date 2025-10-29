"""
Filename: urls.py
Path: src/apps/users/urls.py
Description: URL маршруты для приложения пользователей
"""
from django.urls import path
from .views import UserLoginView, UserLogoutView, UserRegisterView

app_name = 'users'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    # path('register/', UserRegisterView.as_view(), name='register'),
]
