"""
Filename: apps.py
Path: src/apps/tasks/apps.py
Description: Конфигурация приложения задач
"""
from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Конфигурация приложения tasks"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'
    verbose_name = 'Задачи'
