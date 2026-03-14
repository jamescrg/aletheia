from django.db import models
from simple_history.models import HistoricalRecords

from apps.accounts.models import CustomUser
from apps.tasks.models import Task
from utils.models import AuditMixin


class ChecklistFolder(AuditMixin, models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    depth = models.IntegerField(default=0)
    history = HistoricalRecords(table_name="app_checklist_folder_history")

    class Meta:
        db_table = "app_checklist_folder"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.append(current)
            current = current.parent
        ancestors.reverse()
        return ancestors

    def get_descendants(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def can_have_children(self):
        return self.depth < 3

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.parent_id is not None:
            if self.parent_id == self.pk:
                raise ValidationError("A folder cannot be its own parent.")
            if self.parent.depth >= 3:
                raise ValidationError("Maximum folder depth (4 levels) exceeded.")
            current = self.parent
            while current is not None:
                if current.pk == self.pk:
                    raise ValidationError("Circular folder reference detected.")
                current = current.parent
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    def save(self, *args, **kwargs):
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    def update_descendant_depths(self):
        for child in self.children.all():
            child.depth = self.depth + 1
            child.save(update_fields=["depth"])


class ChecklistTemplate(AuditMixin, models.Model):
    name = models.CharField(max_length=100)
    folder = models.ForeignKey(
        ChecklistFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="templates",
    )
    history = HistoricalRecords(table_name="app_checklist_template_history")

    class Meta:
        db_table = "app_checklist_template"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ChecklistTemplateItem(models.Model):
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="items"
    )
    description = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "app_checklist_template_item"
        ordering = ["order", "id"]

    def __str__(self):
        return self.description


class UserChecklistView(models.Model):
    """Tracks when users last viewed a task's checklist."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    last_viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_user_checklist_view"
        unique_together = ("user", "task")

    def __str__(self):
        return f"{self.user.username} viewed {self.task.description} checklist at {self.last_viewed_at}"


class Checklist(AuditMixin, models.Model):
    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="checklist"
    )
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.SET_NULL, null=True
    )
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "app_checklist"

    def __str__(self):
        return f"Checklist: {self.name} for {self.task}"


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name="items"
    )
    description = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "app_checklist_item"
        ordering = ["order", "id"]

    def __str__(self):
        return self.description


def can_complete_task(task):
    try:
        checklist = task.checklist
        return not checklist.items.filter(is_complete=False).exists()
    except Checklist.DoesNotExist:
        return True
