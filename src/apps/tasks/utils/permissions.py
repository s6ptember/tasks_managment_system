"""
Filename: permissions.py
Path: src/apps/tasks/utils/permissions.py
Description: Утилиты для проверки прав доступа
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Базовый миксин для проверки роли пользователя
    Используется для ограничения доступа к представлениям
    """
    required_roles = []

    def test_func(self):
        """Проверка наличия требуемой роли у пользователя"""
        if not self.request.user.is_authenticated:
            return False

        return self.request.user.role in self.required_roles

    def handle_no_permission(self):
        """Обработка отсутствия прав доступа"""
        raise PermissionDenied("У вас нет прав для доступа к этой странице")


class AdminOnlyMixin(RoleRequiredMixin):
    """Доступ только для администраторов"""
    required_roles = ['admin']


class ManagerOrAdminMixin(RoleRequiredMixin):
    """Доступ для менеджеров и администраторов"""
    required_roles = ['admin', 'manager']


class EmployeeOnlyMixin(RoleRequiredMixin):
    """Доступ только для сотрудников"""
    required_roles = ['employee']


def check_task_permission(user, task, action='view'):
    """
    Проверка прав на действие с задачей

    Args:
        user: Пользователь
        task: Задача
        action: Действие ('view', 'edit', 'delete')

    Returns:
        bool: Есть ли права
    """
    # Администраторы имеют полный доступ
    if user.is_admin:
        return True

    # Менеджеры могут редактировать и удалять
    if user.is_manager and action in ['view', 'edit', 'delete']:
        return True

    # Сотрудники могут только просматривать
    if user.is_employee and action == 'view':
        return True

    return False


def check_subtask_permission(user, subtask, action='complete'):
    """
    Проверка прав на действие с подзадачей

    Args:
        user: Пользователь
        subtask: Подзадача
        action: Действие ('complete', 'edit', 'delete')

    Returns:
        bool: Есть ли права
    """
    # Администраторы и менеджеры имеют полный доступ
    if user.can_create_tasks:
        return True

    # Сотрудники могут завершать только свои подзадачи
    if action == 'complete':
        return subtask.assignments.filter(user=user).exists()

    return False
