from django.conf import settings
from django.db import models


class Quiz(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title}"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("quiz", "order")]

    def __str__(self) -> str:
        return f"Q{self.order}: {self.text[:50]}"


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{'✓' if self.is_correct else ' '} {self.text[:50]}"
