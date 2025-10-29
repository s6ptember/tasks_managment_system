"""
Filename: urls_updated.py
Path: src/apps/tasks/urls_updated.py
Description: Обновленные URL маршруты с поддержкой модального окна завершения подзадачи
"""
from django.urls import path
from .views import (
    DashboardView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    TaskDetailView,
    TakeTaskView,
    CompleteSubtaskView,
    SubtaskUpdateView,
    SubtaskDeleteView
)
from .management_views import (
    ManagementDashboardView,
    ManagementTemplateCreateView,
    ManagementTemplateUpdateView,
    ManagementTemplateDeleteView,
    ManagementTaskCreateView
)

app_name = 'tasks'

urlpatterns = [
    # Главная страница
    path('', DashboardView.as_view(), name='dashboard'),

    # CRUD операции для задач
    path('task/create/', TaskCreateView.as_view(), name='task_create'),
    path('task/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    path('task/<int:pk>/edit/', TaskUpdateView.as_view(), name='task_edit'),
    path('task/<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),

    # Операции с задачами
    path('task/<int:pk>/take/', TakeTaskView.as_view(), name='task_take'),

    # Операции с подзадачами - ОБНОВЛЕНО: поддержка GET и POST для модального окна
    path('subtask/<int:pk>/complete/', CompleteSubtaskView.as_view(), name='subtask_complete'),
    path('subtask/<int:pk>/update/', SubtaskUpdateView.as_view(), name='subtask_update'),
    path('subtask/<int:pk>/delete/', SubtaskDeleteView.as_view(), name='subtask_delete'),

    # Панель управления для менеджеров и админов
    path('management/', ManagementDashboardView.as_view(), name='management_dashboard'),

    # Управление шаблонами
    path('management/template/create/', ManagementTemplateCreateView.as_view(), name='management_template_create'),
    path('management/template/<int:pk>/edit/', ManagementTemplateUpdateView.as_view(), name='management_template_edit'),
    path('management/template/<int:pk>/delete/', ManagementTemplateDeleteView.as_view(), name='management_template_delete'),

    # Создание задач через панель управления
    path('management/task/create/', ManagementTaskCreateView.as_view(), name='management_task_create'),
]
