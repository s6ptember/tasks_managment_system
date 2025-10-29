"""
Filename: views.py
Path: src/apps/tasks/views.py
Description: Обновленные представления с режимом "Все задачи"
ОБНОВЛЕНИЯ:
- Добавлен режим отображения всех задач с группировкой по датам
- Поддержка множественных исполнителей на одну подзадачу
"""
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib import messages
from django.db.models import Q, Count
from .models import Task, Subtask, SubtaskAssignment, TaskAction
from .forms import TaskCreateForm, TaskUpdateForm, TakeTaskForm, CompleteSubtaskForm
from apps.temp.models import TaskTemplate, SubtaskTemplateItem


class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав менеджера или администратора"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_create_tasks


class HTMXMixin:
    """Миксин для поддержки HTMX запросов"""

    def is_htmx(self):
        """Проверка, является ли запрос HTMX"""
        return self.request.headers.get('HX-Request') == 'true'


class DashboardView(LoginRequiredMixin, HTMXMixin, ListView):
    """
    Главная страница - дашборд с задачами
    Поддерживает два режима:
    1. По дням (3 дня до текущего, текущий, 3 дня после)
    2. Все задачи (группировка по датам)
    """

    model = Task
    template_name = 'tasks/dashboard.html'
    context_object_name = 'tasks'

    def get_view_mode(self):
        """Получение режима отображения: 'daily' или 'all'"""
        return self.request.GET.get('mode', 'daily')

    def get_queryset(self):
        """Получение задач в зависимости от режима"""
        mode = self.get_view_mode()

        base_queryset = Task.objects.select_related(
            'created_by',
            'template'
        ).prefetch_related(
            'subtasks__assignments__user'
        )

        if mode == 'all':
            # Режим "Все задачи" - от 3 дней назад до +∞
            today = datetime.now().date()
            start_date = today - timedelta(days=3)

            return base_queryset.filter(
                date__gte=start_date
            ).order_by('date', '-created_at')
        else:
            # Режим "По дням" - только выбранная дата
            selected_date = self.get_selected_date()
            return base_queryset.filter(
                date=selected_date
            ).order_by('-created_at')

    def get_selected_date(self):
        """Получение выбранной даты из GET параметра или текущая дата"""
        date_str = self.request.GET.get('date')

        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        return datetime.now().date()

    def get_week_dates(self):
        """
        Генерация дат для навигации: 3 дня до выбранной даты, выбранная дата, 3 дня после
        """
        selected_date = self.get_selected_date()
        today = datetime.now().date()

        week_dates = []
        day_names_short = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        # Генерируем 7 дней: 3 до, текущий, 3 после
        for i in range(-3, 4):
            date = selected_date + timedelta(days=i)
            day_name = day_names_short[date.weekday()]

            week_dates.append({
                'date': date,
                'day_name': day_name,
                'day_number': date.day,
                'is_active': date == selected_date,
                'is_today': date == today
            })

        return week_dates

    def get_grouped_tasks(self):
        """
        Группировка задач по датам для режима "Все задачи"
        Возвращает список групп с датами и задачами
        """
        today = datetime.now().date()
        start_date = today - timedelta(days=3)

        # Получаем все задачи от start_date
        all_tasks = self.get_queryset()

        # Группируем задачи по датам
        tasks_by_date = {}
        for task in all_tasks:
            if task.date not in tasks_by_date:
                tasks_by_date[task.date] = []
            tasks_by_date[task.date].append(task)

        # Получаем все уникальные даты задач
        task_dates = sorted(tasks_by_date.keys())

        if not task_dates:
            return []

        # Находим минимальную и максимальную даты
        min_date = max(start_date, task_dates[0])
        max_date = task_dates[-1]

        # Создаем группы для всех дат в диапазоне
        groups = []
        current_date = min_date

        while current_date <= max_date:
            group = {
                'date': current_date,
                'is_today': current_date == today,
                'tasks': tasks_by_date.get(current_date, []),
                'has_tasks': current_date in tasks_by_date
            }
            groups.append(group)
            current_date += timedelta(days=1)

        return groups

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        mode = self.get_view_mode()

        context['view_mode'] = mode
        context['week_dates'] = self.get_week_dates()
        context['selected_date'] = self.get_selected_date()
        context['can_create_tasks'] = self.request.user.can_create_tasks

        if mode == 'all':
            # Для режима "Все задачи" передаем группированные задачи
            context['grouped_tasks'] = self.get_grouped_tasks()
            # Подсчет активных задач для всего периода
            context['active_tasks_count'] = Task.objects.filter(
                date__gte=datetime.now().date() - timedelta(days=3)
            ).exclude(status='completed').count()
        else:
            # Для режима "По дням" подсчет только для выбранной даты
            context['active_tasks_count'] = Task.objects.filter(
                date=self.get_selected_date()
            ).exclude(status='completed').count()

        return context


class TaskCreateView(LoginRequiredMixin, ManagerRequiredMixin, HTMXMixin, CreateView):
    """
    Создание новой задачи на основе шаблона
    Доступно только менеджерам и администраторам
    С поддержкой динамического редактирования подзадач
    """

    model = Task
    form_class = TaskCreateForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def get_form_kwargs(self):
        """Передача пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        """Обработка GET запроса для отображения формы"""
        self.object = None
        form = self.get_form()

        # Предзаполнение даты из параметра
        if 'date' in request.GET:
            form.initial['date'] = request.GET.get('date')

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        """
        Создание задачи и автоматическое добавление подзадач из выбранных объектов
        """
        with transaction.atomic():
            # Создаем задачу
            form.instance.created_by = self.request.user
            self.object = form.save()

            # Получаем список ID подзадач из формы
            subtask_ids = self.request.POST.getlist('subtask_ids[]')

            # Создаем подзадачи на основе выбранных объектов
            if subtask_ids:
                for order, subtask_id in enumerate(subtask_ids):
                    try:
                        subtask_item = SubtaskTemplateItem.objects.get(id=subtask_id)
                        Subtask.objects.create(
                            task=self.object,
                            name=subtask_item.name,
                            order=order
                        )
                    except SubtaskTemplateItem.DoesNotExist:
                        continue

            # Логируем создание задачи
            template = form.cleaned_data.get('template')
            TaskAction.objects.create(
                task=self.object,
                user=self.request.user,
                action_type=TaskAction.ActionType.CREATED,
                details={
                    'template_name': template.name if template else None,
                    'subtasks_count': len(subtask_ids)
                }
            )

            messages.success(self.request, f'Задача "{self.object.title}" успешно создана')

        # Для HTMX возвращаем обновленный dashboard
        if self.is_htmx():
            return redirect(self.success_url)

        return redirect(self.success_url)


class TaskUpdateView(LoginRequiredMixin, ManagerRequiredMixin, HTMXMixin, UpdateView):
    """
    Редактирование задачи
    Доступно только менеджерам и администраторам
    """

    model = Task
    form_class = TaskUpdateForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def get(self, request, *args, **kwargs):
        """Обработка GET запроса для отображения формы редактирования"""
        self.object = self.get_object()
        form = self.get_form()
        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        """Логирование изменений"""
        changes = {}

        for field in form.changed_data:
            old_value = getattr(self.object, field)
            new_value = form.cleaned_data[field]
            changes[field] = {
                'old': str(old_value),
                'new': str(new_value)
            }

        response = super().form_valid(form)

        if changes:
            TaskAction.objects.create(
                task=self.object,
                user=self.request.user,
                action_type=TaskAction.ActionType.UPDATED,
                details={'changes': changes}
            )

        messages.success(self.request, f'Задача "{self.object.title}" обновлена')

        if self.is_htmx():
            return redirect(self.success_url)

        return response


class TaskDeleteView(LoginRequiredMixin, ManagerRequiredMixin, HTMXMixin, DeleteView):
    """
    Удаление задачи
    Доступно только менеджерам и администраторам
    """

    model = Task
    success_url = reverse_lazy('tasks:dashboard')

    def delete(self, request, *args, **kwargs):
        """Логирование удаления перед самим удалением"""
        self.object = self.get_object()

        TaskAction.objects.create(
            task=self.object,
            user=request.user,
            action_type=TaskAction.ActionType.DELETED,
            details={
                'title': self.object.title,
                'date': str(self.object.date)
            }
        )

        messages.success(request, f'Задача "{self.object.title}" удалена')

        # Удаляем задачу
        task_pk = self.object.pk
        super().delete(request, *args, **kwargs)

        # Для HTMX возвращаем обновленный список задач
        if self.is_htmx():
            return redirect(self.success_url)

        return redirect(self.success_url)


class TaskDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Детальный просмотр задачи со всеми подзадачами"""

    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        """Оптимизированный запрос с подгрузкой связанных данных"""
        return Task.objects.select_related(
            'created_by',
            'template'
        ).prefetch_related(
            'subtasks__assignments__user'
        )


class TakeTaskView(LoginRequiredMixin, HTMXMixin, View):
    """
    Взятие задачи сотрудником, менеджером или админом
    Показывает модальное окно с выбором подзадач
    Поддерживает множественных исполнителей на одну подзадачу
    """

    def get(self, request, pk):
        """Отображение формы выбора подзадач"""
        task = get_object_or_404(Task, pk=pk)
        form = TakeTaskForm(task)

        return render(request, 'tasks/take_task_modal.html', {
            'task': task,
            'form': form
        })

    def post(self, request, pk):
        """Обработка взятия задачи"""
        task = get_object_or_404(Task, pk=pk)
        form = TakeTaskForm(task, request.POST)

        if form.is_valid():
            with transaction.atomic():
                selected_subtasks = form.cleaned_data['subtasks']

                for subtask in selected_subtasks:
                    # Создаем назначение, если еще не существует
                    # Теперь поддерживается множественное назначение
                    assignment, created = SubtaskAssignment.objects.get_or_create(
                        subtask=subtask,
                        user=request.user
                    )

                    # Переводим подзадачу в статус "В процессе"
                    if created and subtask.status == Subtask.Status.PENDING:
                        subtask.mark_in_progress()

                # Логируем взятие задачи
                TaskAction.objects.create(
                    task=task,
                    user=request.user,
                    action_type=TaskAction.ActionType.ASSIGNED,
                    details={
                        'subtasks': [st.name for st in selected_subtasks]
                    }
                )

                messages.success(
                    request,
                    f'Вы взяли {selected_subtasks.count()} подзадач из задачи "{task.title}"'
                )
        else:
            messages.error(request, 'Выберите хотя бы одну подзадачу')

        return redirect('tasks:dashboard')


class CompleteSubtaskView(LoginRequiredMixin, HTMXMixin, View):
    """
    Отметка выполнения подзадачи сотрудником, менеджером или админом
    Доступно только для назначенных исполнителей
    Возвращает модальное окно подтверждения
    """

    def get(self, request, pk):
        """Отображение модального окна подтверждения"""
        subtask = get_object_or_404(Subtask, pk=pk)
        task = subtask.task

        # Проверяем права на завершение
        if not subtask.assignments.filter(user=request.user).exists():
            messages.error(request, 'У вас нет прав на завершение этой подзадачи')
            return redirect('tasks:dashboard')

        return render(request, 'tasks/complete_subtask_modal.html', {
            'subtask': subtask,
            'task': task
        })

    def post(self, request, pk):
        """Завершение подзадачи после подтверждения"""
        subtask = get_object_or_404(Subtask, pk=pk)
        task = subtask.task

        # Проверяем права на завершение
        if subtask.mark_completed(request.user):
            messages.success(request, f'Подзадача "{subtask.name}" отмечена как выполненная')
        else:
            messages.error(request, 'У вас нет прав на завершение этой подзадачи')

        # Для HTMX возвращаем только обновленную карточку задачи
        if self.is_htmx():
            # Перезагружаем задачу с обновленными данными
            task = Task.objects.select_related(
                'created_by',
                'template'
            ).prefetch_related(
                'subtasks__assignments__user'
            ).get(pk=task.pk)

            return render(request, 'tasks/partials/task_card.html', {
                'task': task,
                'user': request.user
            })

        return redirect('tasks:dashboard')


class SubtaskUpdateView(LoginRequiredMixin, View):
    """
    API endpoint для обновления подзадачи
    Используется для редактирования названия и порядка
    """

    def post(self, request, pk):
        """Обновление подзадачи"""
        # Проверка прав
        if not request.user.can_create_tasks:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        subtask = get_object_or_404(Subtask, pk=pk)

        name = request.POST.get('name')
        order = request.POST.get('order')

        if name:
            subtask.name = name

        if order is not None:
            try:
                subtask.order = int(order)
            except ValueError:
                return JsonResponse({'error': 'Некорректный порядок'}, status=400)

        subtask.save()

        return JsonResponse({
            'id': subtask.id,
            'name': subtask.name,
            'order': subtask.order,
            'status': subtask.get_status_display()
        })


class SubtaskDeleteView(LoginRequiredMixin, ManagerRequiredMixin, View):
    """
    Удаление подзадачи
    Доступно только менеджерам и администраторам
    """

    def post(self, request, pk):
        """Удаление подзадачи"""
        subtask = get_object_or_404(Subtask, pk=pk)
        task = subtask.task
        subtask_name = subtask.name

        subtask.delete()

        # Обновляем статус задачи
        task.update_status()

        messages.success(request, f'Подзадача "{subtask_name}" удалена')
        return redirect('tasks:dashboard')
