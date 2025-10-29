"""
Filename: models_updated.py
Path: src/apps/tasks/models_updated.py
Description: Обновленные модели с подсчетом времени выполнения задач
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.temp.models import TaskTemplate


class Task(models.Model):
    """
    Задача на конкретный день
    Создается менеджером/админом на основе шаблона
    """

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Доступна'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершена'

    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )

    date = models.DateField(
        verbose_name='Дата'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='Статус'
    )

    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Шаблон'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name='Создатель'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['date', '-created_at']
        indexes = [
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.date})"

    def update_status(self):
        """
        Автоматическое обновление статуса задачи
        на основе статусов подзадач
        """
        subtasks = self.subtasks.all()

        if not subtasks.exists():
            self.status = self.Status.AVAILABLE
        elif all(st.status == Subtask.Status.COMPLETED for st in subtasks):
            self.status = self.Status.COMPLETED
        elif any(st.status in [Subtask.Status.IN_PROGRESS, Subtask.Status.COMPLETED] for st in subtasks):
            self.status = self.Status.IN_PROGRESS
        else:
            self.status = self.Status.AVAILABLE

        self.save(update_fields=['status', 'updated_at'])

    def get_color_gradient(self):
        """
        Получение цветового градиента для карточки
        Циклическое распределение цветов
        """
        colors = [
            'beige',
            'purple',
            'pink',
            'blue',
            'green'
        ]
        # Используем ID для циклического выбора цвета
        return colors[self.id % len(colors)]


class Subtask(models.Model):
    """
    Подзадача внутри задачи
    Может быть назначена нескольким исполнителям
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершена'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name='Задача'
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время начала'
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время завершения'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Подзадача'
        verbose_name_plural = 'Подзадачи'
        ordering = ['order']

    def __str__(self):
        return f"{self.task.title} - {self.name}"

    def get_assignees(self):
        """Получение списка исполнителей подзадачи"""
        return [assignment.user for assignment in self.assignments.select_related('user')]

    def get_status_indicator_class(self):
        """Получение CSS класса для индикатора статуса"""
        status_map = {
            self.Status.PENDING: 'indicator-gray',
            self.Status.IN_PROGRESS: 'indicator-orange',
            self.Status.COMPLETED: 'indicator-green'
        }
        return status_map.get(self.status, 'indicator-gray')

    def get_duration_minutes(self):
        """Получение длительности выполнения в минутах"""
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return int(duration.total_seconds() / 60)
        return 0

    def get_duration_formatted(self):
        """Форматированное время выполнения"""
        if not self.started_at or not self.completed_at:
            return "Не завершена"

        duration = self.completed_at - self.started_at
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes}м"

    def mark_in_progress(self):
        """Перевести подзадачу в статус "В процессе" """
        if self.status == self.Status.PENDING:
            self.status = self.Status.IN_PROGRESS
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])
            self.task.update_status()

    def mark_completed(self, user):
        """
        Пометить подзадачу как завершенную
        Только если пользователь является исполнителем
        """
        if self.assignments.filter(user=user).exists():
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
            self.task.update_status()

            # Создаем запись о завершении с подсчетом времени
            duration_minutes = self.get_duration_minutes()
            TaskAction.objects.create(
                task=self.task,
                user=user,
                action_type=TaskAction.ActionType.COMPLETED,
                details={
                    'subtask': self.name,
                    'started_at': self.started_at.isoformat() if self.started_at else None,
                    'completed_at': self.completed_at.isoformat(),
                    'duration_minutes': duration_minutes,
                    'duration_formatted': self.get_duration_formatted()
                }
            )

            return True
        return False


class SubtaskAssignment(models.Model):
    """
    Связь между подзадачей и исполнителем
    Поддержка нескольких исполнителей на одну подзадачу
    """

    subtask = models.ForeignKey(
        Subtask,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Подзадача'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subtask_assignments',
        verbose_name='Исполнитель'
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата назначения'
    )

    class Meta:
        verbose_name = 'Назначение подзадачи'
        verbose_name_plural = 'Назначения подзадач'
        unique_together = ['subtask', 'user']

    def __str__(self):
        return f"{self.user.first_name_only} -> {self.subtask.name}"


class TaskAction(models.Model):
    """
    Аудит действий с задачами
    Логирование всех важных изменений с подсчетом времени выполнения
    """

    class ActionType(models.TextChoices):
        CREATED = 'created', 'Создана'
        UPDATED = 'updated', 'Обновлена'
        DELETED = 'deleted', 'Удалена'
        ASSIGNED = 'assigned', 'Назначена'
        COMPLETED = 'completed', 'Завершена'
        STATUS_CHANGED = 'status_changed', 'Статус изменен'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name='Задача'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_actions',
        verbose_name='Пользователь'
    )

    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='Тип действия'
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время'
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Детали'
    )

    class Meta:
        verbose_name = 'Действие с задачей'
        verbose_name_plural = 'Действия с задачами'
        ordering = ['-timestamp']

    def __str__(self):
        # Форматированный вывод с временем выполнения
        if self.action_type == self.ActionType.COMPLETED and 'duration_minutes' in self.details:
            subtask_name = self.details.get('subtask', 'Подзадача')
            duration = self.details.get('duration_formatted', 'N/A')
            started = self.details.get('started_at', '')
            completed = self.details.get('completed_at', '')

            # Форматируем время начала и завершения
            if started and completed:
                from datetime import datetime
                start_time = datetime.fromisoformat(started).strftime('%H:%M')
                end_time = datetime.fromisoformat(completed).strftime('%H:%M')
                time_range = f"{start_time}-{end_time}"
            else:
                time_range = ""

            return f"{self.task.title} - {subtask_name}, выполнил {self.user.first_name_only}, за {duration}, {time_range}"

        return f"{self.user.first_name_only} - {self.get_action_type_display()} - {self.task.title}"

    def get_formatted_description(self):
        """Получение отформатированного описания действия для админки"""
        if self.action_type == self.ActionType.COMPLETED and 'duration_minutes' in self.details:
            subtask_name = self.details.get('subtask', 'Подзадача')
            duration = self.details.get('duration_formatted', 'N/A')
            duration_minutes = self.details.get('duration_minutes', 0)

            started = self.details.get('started_at', '')
            completed = self.details.get('completed_at', '')

            if started and completed:
                from datetime import datetime
                start_dt = datetime.fromisoformat(started)
                end_dt = datetime.fromisoformat(completed)
                start_time = start_dt.strftime('%H:%M')
                end_time = end_dt.strftime('%H:%M')
                date_str = start_dt.strftime('%d.%m.%Y')

                return {
                    'task': self.task.title,
                    'subtask': subtask_name,
                    'user': self.user.first_name_only,
                    'duration': duration,
                    'duration_minutes': duration_minutes,
                    'time_range': f"{start_time}-{end_time}",
                    'date': date_str,
                    'full_text': f"Задача: {self.task.title} - {subtask_name}, выполнил {self.user.first_name_only}, за {duration} ({start_time}-{end_time}), {date_str}"
                }

        return {
            'task': self.task.title,
            'user': self.user.first_name_only,
            'action': self.get_action_type_display(),
            'full_text': f"{self.user.first_name_only} - {self.get_action_type_display()} - {self.task.title}"
        }
