from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuizForm, QuestionForm, OptionFormSet
from .models import Quiz, Question


def signup(request):
    if request.user.is_authenticated:
        return redirect("quiz_list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("quiz_list")
    else:
        form = UserCreationForm()

    return render(request, "quizzes/signup.html", {"form": form})


@login_required
def quiz_list(request):
    quizzes = Quiz.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "quizzes/quiz_list.html", {"quizzes": quizzes})


@login_required
def quiz_create(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.owner = request.user
            quiz.save()
            return redirect("quiz_edit", quiz_id=quiz.id)
    else:
        form = QuizForm()

    return render(request, "quizzes/quiz_create.html", {"form": form})


@login_required
def quiz_edit(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            return redirect("quiz_edit", quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)

    questions = quiz.questions.order_by("order", "id")
    return render(request, "quizzes/quiz_edit.html", {"quiz": quiz, "form": form, "questions": questions})


@login_required
def question_create(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    q = Question(quiz=quiz, order=(quiz.questions.count() + 1))
    if request.method == "POST":
        q_form = QuestionForm(request.POST, instance=q)
        formset = OptionFormSet(request.POST, instance=q)
        if q_form.is_valid() and formset.is_valid():
            q_form.save()
            formset.save()
            return redirect("quiz_edit", quiz_id=quiz.id)
    else:
        q_form = QuestionForm(instance=q)
        formset = OptionFormSet(instance=q)

    return render(
        request,
        "quizzes/question_edit.html",
        {"quiz": quiz, "q_form": q_form, "formset": formset, "is_new": True},
    )


@login_required
def question_edit(request, quiz_id: int, question_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    question = get_object_or_404(Question, id=question_id, quiz=quiz)

    if request.method == "POST":
        q_form = QuestionForm(request.POST, instance=question)
        formset = OptionFormSet(request.POST, instance=question)
        if q_form.is_valid() and formset.is_valid():
            q_form.save()
            formset.save()
            return redirect("quiz_edit", quiz_id=quiz.id)
    else:
        q_form = QuestionForm(instance=question)
        formset = OptionFormSet(instance=question)

    return render(
        request,
        "quizzes/question_edit.html",
        {"quiz": quiz, "q_form": q_form, "formset": formset, "is_new": False},
    )


@login_required
def question_delete(request, quiz_id: int, question_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    question = get_object_or_404(Question, id=question_id, quiz=quiz)

    if request.method == "POST":
        question.delete()
        return redirect("quiz_edit", quiz_id=quiz.id)

    return render(request, "quizzes/question_delete.html", {"quiz": quiz, "question": question})
