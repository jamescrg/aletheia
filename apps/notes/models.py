from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.matters.models import Matter

User = get_user_model()


class Note(models.Model):
    """Rich markdown note for a matter with inline document/highlight references."""

    CATEGORY_CHOICES = [
        ("analysis", "Analysis"),
        ("drafting", "Drafting"),
        ("interview", "Interview"),
        ("issue", "Issue"),
        ("note", "Note"),
    ]

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="note")
    date = models.DateField(default=timezone.localdate)
    content = models.TextField(blank=True, default="")  # Markdown content

    # Source references (tracked separately from inline [[doc:id]] syntax)
    documents = models.ManyToManyField(
        "case.Document", blank=True, related_name="notes"
    )
    highlights = models.ManyToManyField(
        "case.Highlight", blank=True, related_name="notes"
    )

    importance = models.PositiveIntegerField(default=5)
    viewed_at = models.DateTimeField(null=True, blank=True)
    labels = models.ManyToManyField("case.Label", related_name="notes", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "app_note"
        ordering = ["-updated_at"]
