"""
Filename: models.py
Path: src/apps/users/models.py
Description: Модели пользователей с ролевой системой
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя с поддержкой ролей

    Роли:
    - admin: Главный администратор (полный доступ)
    - manager: Менеджер (создание и управление задачами)
    - employee: Сотрудник (выполнение задач)
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        MANAGER = 'manager', 'Менеджер'
        EMPLOYEE = 'employee', 'Сотрудник'

    full_name = models.CharField(
        max_length=255,
        verbose_name='Полное имя'
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Роль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name or self.username

    @property
    def is_admin(self):
        """Проверка, является ли пользователь администратором"""
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self):
        """Проверка, является ли пользователь менеджером"""
        return self.role == self.Role.MANAGER

    @property
    def is_employee(self):
        """Проверка, является ли пользователь сотрудником"""
        return self.role == self.Role.EMPLOYEE

    @property
    def can_create_tasks(self):
        """Проверка прав на создание задач"""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]

    @property
    def can_manage_templates(self):
        """Проверка прав на управление шаблонами"""
        return self.role == self.Role.ADMIN

    @property
    def first_name_only(self):
        """Получение только имени (без фамилии)"""
        return self.full_name.split()[0] if self.full_name else self.username
