"""
Filename: apps.py
Path: src/apps/temp/apps.py
Description: Конфигурация приложения шаблонов задач
"""
from django.apps import AppConfig


class TemplatesConfig(AppConfig):
    """Конфигурация приложения templates"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.temp'
    verbose_name = 'Шаблоны задач'
