"""
Filename: helpers.py
Path: src/apps/tasks/utils/helpers.py
Description: Вспомогательные функции для работы с задачами
"""
from datetime import datetime, timedelta
from django.utils import timezone


def get_week_dates(selected_date=None):
    """
    Получение списка дат для недели

    Args:
        selected_date: Выбранная дата (по умолчанию - сегодня)

    Returns:
        list: Список словарей с информацией о днях недели
    """
    if selected_date is None:
        selected_date = timezone.now().date()

    # Находим понедельник текущей недели
    start_of_week = selected_date - timedelta(days=selected_date.weekday())

    week_dates = []
    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    for i in range(7):
        date = start_of_week + timedelta(days=i)
        week_dates.append({
            'date': date,
            'day_name': day_names[i],
            'day_number': date.day,
            'is_active': date == selected_date,
            'is_today': date == timezone.now().date()
        })

    return week_dates


def get_date_from_string(date_string):
    """
    Преобразование строки даты в объект date

    Args:
        date_string: Строка даты в формате 'YYYY-MM-DD'

    Returns:
        date or None: Объект даты или None при ошибке
    """
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def calculate_task_progress(task):
    """
    Расчет прогресса выполнения задачи

    Args:
        task: Объект задачи

    Returns:
        dict: Информация о прогрессе
    """
    subtasks = task.subtasks.all()
    total_subtasks = subtasks.count()

    if total_subtasks == 0:
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

    percentage = int((completed / total_subtasks) * 100)

    return {
        'percentage': percentage,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'total': total_subtasks
    }


def get_available_colors():
    """
    Получение списка доступных цветов для карточек задач

    Returns:
        list: Список названий цветов
    """
    return ['beige', 'purple', 'pink', 'blue', 'green']


def assign_color_to_task(task):
    """
    Назначение цвета задаче на основе её ID

    Args:
        task: Объект задачи

    Returns:
        str: Название цвета
    """
    colors = get_available_colors()
    return colors[task.id % len(colors)]


def format_time_spent(started_at, completed_at=None):
    """
    Форматирование времени, затраченного на подзадачу

    Args:
        started_at: Время начала
        completed_at: Время завершения (опционально)

    Returns:
        str: Форматированное время
    """
    if not started_at:
        return "Не начата"

    end_time = completed_at or timezone.now()
    duration = end_time - started_at

    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)

    if hours > 0:
        return f"{hours}ч {minutes}м"
    return f"{minutes}м"


def get_task_statistics(tasks_queryset):
    """
    Получение статистики по задачам

    Args:
        tasks_queryset: QuerySet задач

    Returns:
        dict: Статистика
    """
    total_tasks = tasks_queryset.count()

    return {
        'total': total_tasks,
        'available': tasks_queryset.filter(status='available').count(),
        'in_progress': tasks_queryset.filter(status='in_progress').count(),
        'completed': tasks_queryset.filter(status='completed').count(),
    }


def can_user_complete_task(user, task):
    """
    Проверка, может ли пользователь завершить задачу

    Args:
        user: Пользователь
        task: Задача

    Returns:
        bool: Может ли завершить
    """
    # Менеджеры и админы могут завершать любые задачи
    if user.can_create_tasks:
        return True

    # Сотрудники могут завершать, если назначены на все подзадачи
    subtasks = task.subtasks.all()

    if not subtasks.exists():
        return False

    # Проверяем, назначен ли пользователь на все подзадачи
    for subtask in subtasks:
        if not subtask.assignments.filter(user=user).exists():
            return False

    return True
