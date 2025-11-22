import django_filters
from django.db.models import F

from apps.accounts.models import CustomUser
from apps.agenda.tasks.models import Task
from apps.matters.models import Matter

STATUS_CHOICES = (
    ("Pending", "Pending"),
    ("Complete", "Complete"),
)


class TasksOrderingFilter(django_filters.OrderingFilter):
    def filter(self, qs, value):
        if value in (None, ""):
            return qs
        ordering = [self.get_ordering_value(param) for param in value]
        try:
            if ordering[0] == "date_due":
                return qs.order_by(
                    F("date_due").asc(nulls_first=True),
                    "priority",
                    "matter__name",
                    "description",
                    "id",
                    "id",
                )
            if ordering[0] == "priority":
                return qs.order_by(
                    "-status",
                    "priority",
                    "matter__name",
                    "description",
                    "id",
                )
            return qs.order_by("-status", *ordering, "id")
        except IndexError:
            return qs.order_by("-status", *ordering, "id")


class TasksFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=STATUS_CHOICES, empty_label="All")
    date_due = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"})
    )
    matter = django_filters.ModelChoiceFilter(
        queryset=Matter.objects.filter(status__in=["Pending", "Open"]).order_by("name"),
        empty_label="All",
    )
    user = django_filters.ModelChoiceFilter(
        queryset=CustomUser.objects.filter(is_active=True).order_by("username"),
        empty_label="All",
    )
    priority = django_filters.NumberFilter(
        field_name="priority",
        lookup_expr="lte",
        label="Priority (≤)",
    )

    order_by = TasksOrderingFilter(
        fields=(
            ("date_due", "date_due"),
            ("priority", "priority"),
        ),
    )

    class Meta:
        model = Task
        fields = [
            "status",
            "priority",
            "matter",
            "user",
            "date_due",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize user field to show title case usernames
        self.filters["user"].field.label_from_instance = (
            lambda obj: obj.username.title()
        )
