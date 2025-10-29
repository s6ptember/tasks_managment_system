"""
Filename: views.py
Path: src/apps/temp/views.py
Description: API представления для работы с шаблонами задач и объектами подзадач
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from .models import TaskTemplate, SubtaskTemplate, SubtaskTemplateItem


class AdminRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав администратора"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_templates


class TaskTemplateListView(LoginRequiredMixin, ListView):
    """Список доступных шаблонов задач"""

    model = TaskTemplate
    context_object_name = 'templates'

    def get_queryset(self):
        """Фильтрация шаблонов в зависимости от роли пользователя"""
        queryset = TaskTemplate.objects.filter(is_active=True).select_related('created_by')

        # Менеджеры видят только доступные им шаблоны
        if not self.request.user.can_manage_templates:
            queryset = queryset.filter(available_for_managers=True)

        return queryset.prefetch_related('subtask_templates__subtask_item')


class TaskTemplateCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Создание нового шаблона задачи (только для администратора)"""

    model = TaskTemplate
    fields = ['name', 'description', 'available_for_managers']
    success_url = reverse_lazy('templates:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TaskTemplateUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Редактирование шаблона задачи (только для администратора)"""

    model = TaskTemplate
    fields = ['name', 'description', 'is_active', 'available_for_managers']
    success_url = reverse_lazy('templates:list')


class TaskTemplateDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление шаблона задачи (только для администратора)"""

    model = TaskTemplate
    success_url = reverse_lazy('templates:list')


class TaskTemplateDetailAPIView(LoginRequiredMixin, View):
    """API endpoint для получения деталей шаблона задачи"""

    def get(self, request, pk):
        """Возвращает JSON с подзадачами шаблона"""
        try:
            template = TaskTemplate.objects.prefetch_related(
                'subtask_templates__subtask_item'
            ).get(pk=pk)

            # Проверка доступа
            if not request.user.can_manage_templates and not template.available_for_managers:
                return JsonResponse({'error': 'Доступ запрещен'}, status=403)

            subtasks = [
                {
                    'id': st.subtask_item.id,
                    'name': st.subtask_item.name,
                    'order': st.order
                }
                for st in template.get_subtask_templates()
            ]

            return JsonResponse({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'subtasks': subtasks
            })

        except TaskTemplate.DoesNotExist:
            return JsonResponse({'error': 'Шаблон не найден'}, status=404)


class SubtaskItemListAPIView(LoginRequiredMixin, View):
    """API endpoint для получения списка всех объектов подзадач"""

    def get(self, request):
        """Возвращает JSON со списком всех активных объектов подзадач"""
        subtask_items = SubtaskTemplateItem.objects.filter(is_active=True).order_by('name')

        items = [
            {
                'id': item.id,
                'name': item.name,
                'description': item.description
            }
            for item in subtask_items
        ]

        return JsonResponse(items, safe=False)
