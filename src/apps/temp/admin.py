"""
Filename: admin.py
Path: src/apps/temp/admin.py
Description: Административная панель для управления шаблонами задач и объектами подзадач
"""
from django.contrib import admin
from .models import TaskTemplate, SubtaskTemplate, SubtaskTemplateItem


@admin.register(SubtaskTemplateItem)
class SubtaskTemplateItemAdmin(admin.ModelAdmin):
    """Административная панель для объектов шаблонов подзадач"""

    list_display = ['name', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class SubtaskTemplateInline(admin.TabularInline):
    """Встроенная форма для подзадач шаблона"""
    model = SubtaskTemplate
    extra = 1
    fields = ['subtask_item', 'order']
    autocomplete_fields = ['subtask_item']


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    """Административная панель для шаблонов задач"""

    list_display = ['name', 'is_active', 'available_for_managers', 'created_by', 'created_at']
    list_filter = ['is_active', 'available_for_managers', 'created_at']
    search_fields = ['name', 'description']
    inlines = [SubtaskTemplateInline]

    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SubtaskTemplate)
class SubtaskTemplateAdmin(admin.ModelAdmin):
    """Административная панель для связей подзадач с шаблонами"""

    list_display = ['task_template', 'subtask_item', 'order', 'created_at']
    list_filter = ['task_template', 'created_at']
    search_fields = ['task_template__name', 'subtask_item__name']
    ordering = ['task_template', 'order']
    autocomplete_fields = ['task_template', 'subtask_item']
