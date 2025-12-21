from django.contrib import admin
from .models import Session, Participant, ParticipantAnswer


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "quiz", "status", "current_question", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("code", "quiz__title")


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "session", "score", "joined_at")
    list_filter = ("session",)
    search_fields = ("name", "session__code")


@admin.register(ParticipantAnswer)
class ParticipantAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "participant", "question", "option", "is_correct", "answered_at")
    list_filter = ("is_correct", "answered_at")
