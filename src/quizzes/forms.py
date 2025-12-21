from django import forms
from django.forms import inlineformset_factory

from .models import Quiz, Question, Option


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: История Казани"}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["order", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Текст вопроса..."}),
        }


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ["text", "is_correct"]
        widgets = {
            "text": forms.TextInput(attrs={"placeholder": "Вариант ответа..."}),
        }


OptionFormSet = inlineformset_factory(
    Question,
    Option,
    form=OptionForm,
    extra=2,
    can_delete=True,
)
