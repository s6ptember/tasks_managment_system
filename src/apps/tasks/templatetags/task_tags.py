"""
Filename: task_tags.py
Path: src/apps/tasks/templatetags/task_tags.py
Description: Кастомные template tags для работы с задачами
"""
from django import template

register = template.Library()


@register.filter
def count_completed(subtasks):
    """Подсчет завершенных подзадач"""
    return subtasks.filter(status='completed').count()


@register.filter
def is_assigned_to(subtask, user):
    """Проверка, назначена ли подзадача пользователю"""
    return subtask.assignments.filter(user=user).exists()


@register.simple_tag
def task_progress(task):
    """Получение прогресса выполнения задачи"""
    subtasks = task.subtasks.all()
    total = subtasks.count()

    if total == 0:
        return {
            'percentage': 0,
            'completed': 0,
            'in_progress': 0,
            'pending': 0,
            'total': 0
        }

    completed = subtasks.filter(status='completed').count()
    in_progress = subtasks.filter(status='in_progress').count()
    pending = subtasks.filter(status='pending').count()

    percentage = int((completed / total) * 100)

    return {
        'percentage': percentage,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'total': total
    }
