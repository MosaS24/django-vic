from django.contrib import admin
from .models import Quiz, Question, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "owner__username")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "order", "text")
    list_filter = ("quiz",)
    ordering = ("quiz", "order")
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "is_correct")
    list_filter = ("is_correct",)
