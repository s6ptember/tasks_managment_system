"""
Filename: forms.py
Path: src/apps/tasks/forms.py
Description: Формы для создания и редактирования задач с автозаполнением из шаблона
"""
from django import forms
from .models import Task, Subtask, SubtaskAssignment
from apps.temp.models import TaskTemplate
from apps.users.models import User


class TaskCreateForm(forms.ModelForm):
    """
    Форма создания задачи из шаблона
    Доступна менеджерам и администраторам
    С автоматическим заполнением полей из шаблона
    """

    template = forms.ModelChoiceField(
        queryset=TaskTemplate.objects.filter(is_active=True),
        required=True,
        label='Шаблон задачи',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'x-on:change': 'loadTemplateData($event.target.value)'
        })
    )

    class Meta:
        model = Task
        fields = ['title', 'date', 'template']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название задачи',
                'id': 'id_title',
                'x-model': 'taskTitle'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'id': 'id_date'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Фильтруем шаблоны в зависимости от роли пользователя
        if user and not user.can_manage_templates:
            self.fields['template'].queryset = TaskTemplate.objects.filter(
                is_active=True,
                available_for_managers=True
            )


class TaskUpdateForm(forms.ModelForm):
    """
    Форма редактирования задачи
    Менеджеры и админы могут изменять название и дату
    """

    class Meta:
        model = Task
        fields = ['title', 'date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название задачи'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class SubtaskUpdateForm(forms.ModelForm):
    """
    Форма обновления подзадачи
    Используется для изменения названия и порядка
    """

    class Meta:
        model = Subtask
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название подзадачи'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }


class TakeTaskForm(forms.Form):
    """
    Форма для взятия задачи сотрудником
    Позволяет выбрать несколько подзадач через чекбоксы
    """

    subtasks = forms.ModelMultipleChoiceField(
        queryset=Subtask.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Выберите подзадачи'
    )

    def __init__(self, task, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только доступные подзадачи (не завершенные)
        self.fields['subtasks'].queryset = task.subtasks.exclude(
            status=Subtask.Status.COMPLETED
        )


class CompleteSubtaskForm(forms.Form):
    """
    Форма для отметки выполнения подзадачи
    Используется сотрудниками для завершения своих задач
    """

    subtask_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_subtask_id(self):
        """Валидация прав на завершение подзадачи"""
        subtask_id = self.cleaned_data['subtask_id']

        try:
            subtask = Subtask.objects.get(id=subtask_id)

            # Проверяем, что пользователь назначен на эту подзадачу
            if not subtask.assignments.filter(user=self.user).exists():
                raise forms.ValidationError('Вы не назначены на эту подзадачу')

            # Проверяем, что подзадача еще не завершена
            if subtask.status == Subtask.Status.COMPLETED:
                raise forms.ValidationError('Подзадача уже завершена')

            return subtask_id

        except Subtask.DoesNotExist:
            raise forms.ValidationError('Подзадача не найдена')
