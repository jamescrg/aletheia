from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.calendar.models import Event


class EventAdmin(SimpleHistoryAdmin):
    list_display = ("id", "date", "matter", "description")


admin.site.register(Event, EventAdmin)
