"""
Filename: views.py
Path: src/apps/users/views.py
Description: Представления для аутентификации пользователей
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import UserLoginForm, UserRegistrationForm
from .models import User


class UserLoginView(LoginView):
    """Представление для входа пользователя"""

    template_name = 'users/login.html'
    form_class = UserLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks:dashboard')


class UserLogoutView(LogoutView):
    """Представление для выхода пользователя"""

    next_page = reverse_lazy('users:login')


class UserRegisterView(CreateView):
    """Представление для регистрации нового пользователя"""

    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
