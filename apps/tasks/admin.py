from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.tasks.models import Task


class TaskAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "user",
        "description",
        "status",
        "matter",
    )


admin.site.register(Task, TaskAdmin)
