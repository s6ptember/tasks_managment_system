"""
Filename: management_views.py
Path: src/apps/tasks/management_views.py
Description: Представления для кастомной страницы управления менеджерами
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from .models import Task, Subtask, TaskAction
from .forms import TaskCreateForm, TaskUpdateForm
from .utils.permissions import ManagerOrAdminMixin
from apps.temp.models import TaskTemplate, SubtaskTemplate
from django import forms


class TaskTemplateForm(forms.ModelForm):
    """Форма для создания и редактирования шаблонов"""

    class Meta:
        model = TaskTemplate
        fields = ['name', 'description', 'is_active', 'available_for_managers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Название шаблона'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Описание шаблона',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'available_for_managers': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }


class SubtaskTemplateFormSet(forms.BaseInlineFormSet):
    """Формсет для подзадач шаблона"""
    pass


class ManagementDashboardView(LoginRequiredMixin, ManagerOrAdminMixin, TemplateView):
    """
    Главная страница управления для менеджеров и админов
    Доступ к созданию задач и шаблонов
    """
    template_name = 'tasks/management/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем список всех шаблонов
        if self.request.user.can_manage_templates:
            context['templates'] = TaskTemplate.objects.all().prefetch_related('subtask_templates')
        else:
            context['templates'] = TaskTemplate.objects.filter(
                is_active=True,
                available_for_managers=True
            ).prefetch_related('subtask_templates')

        # Статистика по задачам
        context['total_tasks'] = Task.objects.count()
        context['active_tasks'] = Task.objects.filter(status='in_progress').count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()

        return context


class ManagementTemplateCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    """
    Создание нового шаблона задачи
    Доступно менеджерам и админам
    """
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'tasks/management/template_form.html'
    success_url = reverse_lazy('tasks:management_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Обработка подзадач из POST данных
        subtask_names = self.request.POST.getlist('subtask_name[]')
        subtask_orders = self.request.POST.getlist('subtask_order[]')

        for i, name in enumerate(subtask_names):
            if name.strip():
                SubtaskTemplate.objects.create(
                    task_template=self.object,
                    name=name.strip(),
                    order=int(subtask_orders[i]) if i < len(subtask_orders) else i
                )

        messages.success(self.request, f'Шаблон "{self.object.name}" успешно создан')
        return response


class ManagementTemplateUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    """
    Редактирование шаблона задачи
    Доступно менеджерам и админам
    """
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'tasks/management/template_form.html'
    success_url = reverse_lazy('tasks:management_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        context['subtasks'] = self.object.subtask_templates.all().order_by('order')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # Удаляем старые подзадачи
        self.object.subtask_templates.all().delete()

        # Создаем новые подзадачи
        subtask_names = self.request.POST.getlist('subtask_name[]')
        subtask_orders = self.request.POST.getlist('subtask_order[]')

        for i, name in enumerate(subtask_names):
            if name.strip():
                SubtaskTemplate.objects.create(
                    task_template=self.object,
                    name=name.strip(),
                    order=int(subtask_orders[i]) if i < len(subtask_orders) else i
                )

        messages.success(self.request, f'Шаблон "{self.object.name}" успешно обновлен')
        return response


class ManagementTemplateDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    """
    Удаление шаблона задачи
    Доступно менеджерам и админам
    """
    model = TaskTemplate
    success_url = reverse_lazy('tasks:management_dashboard')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        template_name = self.object.name

        messages.success(request, f'Шаблон "{template_name}" удален')
        return super().delete(request, *args, **kwargs)


class ManagementTaskCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    """
    Создание задачи через страницу управления
    Может создаваться как из шаблона, так и вручную
    """
    model = Task
    form_class = TaskCreateForm
    template_name = 'tasks/management/task_create.html'
    success_url = reverse_lazy('tasks:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Флаг для определения, создается ли задача вручную
        context['manual_creation'] = self.request.GET.get('manual') == '1'
        return context

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()

            # Если выбран шаблон, создаем подзадачи из него
            if form.cleaned_data.get('template'):
                template = form.cleaned_data['template']

                for subtask_template in template.get_subtask_templates():
                    Subtask.objects.create(
                        task=self.object,
                        name=subtask_template.name,
                        order=subtask_template.order
                    )

                # Логируем создание задачи
                TaskAction.objects.create(
                    task=self.object,
                    user=self.request.user,
                    action_type=TaskAction.ActionType.CREATED,
                    details={
                        'template_name': template.name,
                        'subtasks_count': template.subtask_templates.count()
                    }
                )
            else:
                # Создание задачи вручную - обработка подзадач из формы
                subtask_names = self.request.POST.getlist('subtask_name[]')

                for i, name in enumerate(subtask_names):
                    if name.strip():
                        Subtask.objects.create(
                            task=self.object,
                            name=name.strip(),
                            order=i
                        )

                TaskAction.objects.create(
                    task=self.object,
                    user=self.request.user,
                    action_type=TaskAction.ActionType.CREATED,
                    details={'manual_creation': True}
                )

            messages.success(self.request, f'Задача "{self.object.title}" успешно создана')

        return redirect(self.success_url)
