"""
Filename: models.py
Path: src/apps/temp/models.py
Description: Модели для шаблонов задач и подзадач с поддержкой объектов подзадач
"""
from django.db import models
from django.conf import settings


class SubtaskTemplateItem(models.Model):
    """
    Независимый шаблон подзадачи (объект)
    Может использоваться в разных шаблонах задач
    """

    name = models.CharField(
        max_length=255,
        verbose_name='Название подзадачи'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_subtask_template_items',
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
        verbose_name = 'Объект шаблона подзадачи'
        verbose_name_plural = 'Объекты шаблонов подзадач'
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskTemplate(models.Model):
    """
    Шаблон (заготовка) задачи
    Создается администратором и используется менеджерами для быстрого создания задач
    """

    name = models.CharField(
        max_length=255,
        verbose_name='Название шаблона'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    available_for_managers = models.BooleanField(
        default=True,
        verbose_name='Доступен менеджерам'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_templates',
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
        verbose_name = 'Шаблон задачи'
        verbose_name_plural = 'Шаблоны задач'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_subtask_templates(self):
        """Получение всех подзадач шаблона в правильном порядке"""
        return self.subtask_templates.all().order_by('order')


class SubtaskTemplate(models.Model):
    """
    Связь между шаблоном задачи и объектом шаблона подзадачи
    Определяет какие подзадачи входят в шаблон задачи и их порядок
    """

    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='subtask_templates',
        verbose_name='Шаблон задачи'
    )

    subtask_item = models.ForeignKey(
        SubtaskTemplateItem,
        on_delete=models.CASCADE,
        related_name='template_usages',
        verbose_name='Объект подзадачи'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Подзадача в шаблоне'
        verbose_name_plural = 'Подзадачи в шаблонах'
        ordering = ['order']
        unique_together = ['task_template', 'subtask_item']

    def __str__(self):
        return f"{self.task_template.name} - {self.subtask_item.name}"

    @property
    def name(self):
        """Для обратной совместимости"""
        return self.subtask_item.name
