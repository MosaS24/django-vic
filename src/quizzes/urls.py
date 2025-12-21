from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),

    path("quizzes/", views.quiz_list, name="quiz_list"),
    path("quizzes/new/", views.quiz_create, name="quiz_create"),
    path("quizzes/<int:quiz_id>/edit/", views.quiz_edit, name="quiz_edit"),

    path("quizzes/<int:quiz_id>/questions/new/", views.question_create, name="question_create"),
    path("quizzes/<int:quiz_id>/questions/<int:question_id>/edit/", views.question_edit, name="question_edit"),
    path("quizzes/<int:quiz_id>/questions/<int:question_id>/delete/", views.question_delete, name="question_delete"),
]
