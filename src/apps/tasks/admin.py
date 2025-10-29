"""
Filename: admin_updated.py
Path: src/apps/tasks/admin_updated.py
Description: Обновленная административная панель с подсчетом времени выполнения и отображением исполнителей
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Task, Subtask, SubtaskAssignment, TaskAction


class SubtaskInline(admin.TabularInline):
    """Встроенная форма для подзадач"""
    model = Subtask
    extra = 0
    fields = ['name', 'status', 'order', 'started_at', 'completed_at', 'duration_display']
    readonly_fields = ['duration_display']

    def duration_display(self, obj):
        """Отображение времени выполнения с исполнителями"""
        # Получаем всех исполнителей
        assignees = obj.assignments.select_related('user').all()
        assignees_names = ', '.join([a.user.full_name for a in assignees]) if assignees else 'Не назначено'

        if obj.started_at and obj.completed_at:
            duration = obj.get_duration_formatted()
            minutes = obj.get_duration_minutes()
            start_time = obj.started_at.strftime('%H:%M')
            end_time = obj.completed_at.strftime('%H:%M')

            return format_html(
                '<span style="color: white; font-weight: bold;">{}</span> | '
                '<span style="color: green; font-weight: bold;">{}</span> ({}-{})',
                assignees_names,
                duration,
                start_time,
                end_time
            )
        elif obj.started_at:
            return format_html(
                '<span style="color: white; font-weight: bold;">{}</span> | '
                '<span style="color: orange;">В процессе</span>',
                assignees_names
            )
        return format_html(
            '<span style="color: white; font-weight: bold;">{}</span> | '
            '<span style="color: gray;">Не начата</span>',
            assignees_names
        )

    duration_display.short_description = 'Исполнители и время выполнения'


class SubtaskAssignmentInline(admin.TabularInline):
    """Встроенная форма для назначений подзадач"""
    model = SubtaskAssignment
    extra = 0
    fields = ['user', 'assigned_at']
    readonly_fields = ['assigned_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Административная панель для задач"""

    list_display = ['title', 'date', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'date', 'created_at']
    search_fields = ['title', 'created_by__full_name']
    date_hierarchy = 'date'
    inlines = [SubtaskInline]

    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    """Административная панель для подзадач с отображением времени"""

    list_display = [
        'name',
        'task',
        'status',
        'order',
        'assignees_display',
        'duration_display',
        'time_range_display'
    ]
    list_filter = ['status', 'task__date']
    search_fields = ['name', 'task__title']
    inlines = [SubtaskAssignmentInline]
    readonly_fields = ['duration_display', 'time_range_display']

    def assignees_display(self, obj):
        """Отображение исполнителей"""
        assignees = obj.assignments.select_related('user').all()
        if assignees:
            names = [a.user.first_name_only for a in assignees]
            return ', '.join(names)
        return '-'

    assignees_display.short_description = 'Исполнители'

    def duration_display(self, obj):
        """Отображение времени выполнения"""
        if obj.started_at and obj.completed_at:
            duration = obj.get_duration_formatted()
            minutes = obj.get_duration_minutes()

            color = 'green' if obj.status == 'completed' else 'orange'
            return format_html(
                '<strong style="color: {};">{}</strong> ({}мин)',
                color,
                duration,
                minutes
            )
        elif obj.started_at:
            return format_html('<span style="color: orange;">В процессе</span>')
        return '-'

    duration_display.short_description = 'Длительность'

    def time_range_display(self, obj):
        """Отображение временного диапазона"""
        if obj.started_at and obj.completed_at:
            start_time = obj.started_at.strftime('%H:%M')
            end_time = obj.completed_at.strftime('%H:%M')
            date_str = obj.started_at.strftime('%d.%m.%Y')

            return format_html(
                '{}<br><small style="color: gray;">{}</small>',
                f"{start_time} - {end_time}",
                date_str
            )
        elif obj.started_at:
            start_time = obj.started_at.strftime('%H:%M, %d.%m.%Y')
            return format_html(
                'Начато: {}<br><small style="color: orange;">В процессе</small>',
                start_time
            )
        return '-'

    time_range_display.short_description = 'Время'


@admin.register(SubtaskAssignment)
class SubtaskAssignmentAdmin(admin.ModelAdmin):
    """Административная панель для назначений подзадач"""

    list_display = ['subtask', 'user', 'assigned_at']
    list_filter = ['assigned_at', 'user']
    search_fields = ['subtask__name', 'user__full_name']


@admin.register(TaskAction)
class TaskActionAdmin(admin.ModelAdmin):
    """Административная панель для аудита действий с форматированием времени"""

    list_display = [
        'task',
        'user',
        'action_type',
        'formatted_info',
        'timestamp'
    ]
    list_filter = ['action_type', 'timestamp', 'user']
    search_fields = ['task__title', 'user__full_name']
    readonly_fields = [
        'task',
        'user',
        'action_type',
        'timestamp',
        'details',
        'formatted_display'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('task', 'user', 'action_type', 'timestamp')
        }),
        ('Детали', {
            'fields': ('formatted_display', 'details'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Запрет на добавление записей аудита вручную"""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрет на изменение записей аудита"""
        return False

    def formatted_info(self, obj):
        """Форматированная информация о действии"""
        formatted = obj.get_formatted_description()

        if obj.action_type == 'completed' and 'duration' in formatted:
            return format_html(
                '<strong>{}</strong><br>'
                '<span style="color: green;">Подзадача: {}</span><br>'
                '<span style="color: blue;">Длительность: {}</span><br>'
                '<span style="color: gray;">Время: {} ({})</span>',
                formatted.get('user', ''),
                formatted.get('subtask', ''),
                formatted.get('duration', ''),
                formatted.get('time_range', ''),
                formatted.get('date', '')
            )

        return formatted.get('full_text', str(obj))

    formatted_info.short_description = 'Информация'

    def formatted_display(self, obj):
        """Детальное отформатированное отображение для страницы редактирования"""
        formatted = obj.get_formatted_description()

        if obj.action_type == 'completed' and 'duration' in formatted:
            html = f"""
            <div style="padding: 15px; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 4px;">
                <h3 style="margin-top: 0; color: #1e40af;">Завершение задачи</h3>
                <p><strong>Задача:</strong> {formatted.get('task', '')}</p>
                <p><strong>Подзадача:</strong> {formatted.get('subtask', '')}</p>
                <p><strong>Исполнитель:</strong> {formatted.get('user', '')}</p>
                <p style="color: #059669;"><strong>Длительность:</strong> {formatted.get('duration', '')} ({formatted.get('duration_minutes', 0)} минут)</p>
                <p><strong>Время выполнения:</strong> {formatted.get('time_range', '')}</p>
                <p><strong>Дата:</strong> {formatted.get('date', '')}</p>
            </div>
            """
            return format_html(html)

        return format_html(
            '<div style="padding: 10px; background: #f9fafb; border-radius: 4px;">{}</div>',
            formatted.get('full_text', str(obj))
        )

    formatted_display.short_description = 'Форматированное отображение'
