"""
Filename: urls.py
Path: src/apps/temp/urls.py
Description: URL маршруты для приложения шаблонов задач
"""
from django.urls import path
from .views import (
    TaskTemplateListView,
    TaskTemplateCreateView,
    TaskTemplateUpdateView,
    TaskTemplateDeleteView,
    TaskTemplateDetailAPIView,
    SubtaskItemListAPIView
)

app_name = 'templates'

urlpatterns = [
    path('', TaskTemplateListView.as_view(), name='list'),
    path('create/', TaskTemplateCreateView.as_view(), name='create'),
    path('<int:pk>/', TaskTemplateDetailAPIView.as_view(), name='detail'),
    path('<int:pk>/edit/', TaskTemplateUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', TaskTemplateDeleteView.as_view(), name='delete'),

    # API endpoint для получения списка объектов подзадач
    path('subtask-items/', SubtaskItemListAPIView.as_view(), name='subtask_items_list'),
]
