"""
Filename: apps.py
Path: src/apps/users/apps.py
Description: Конфигурация приложения пользователей
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения users"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Пользователи'
