from django.db import models
from django.utils import timezone

from quizzes.models import Quiz, Question, Option


class Session(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        RUNNING = "running", "Running"
        FINISHED = "finished", "Finished"

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    code = models.CharField(max_length=12, unique=True)  # например: AB12CD
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
    )
    current_question = models.ForeignKey(
        Question,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Session {self.code} ({self.quiz.title})"


class Participant(models.Model):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    name = models.CharField(max_length=50)
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "name")]
        ordering = ["-score", "joined_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.session.code})"


class ParticipantAnswer(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="+",
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="+",
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("participant", "question")]
        ordering = ["answered_at"]

    def __str__(self) -> str:
        return f"{self.participant.name}: Q{self.question.id} -> {self.option.id}"
