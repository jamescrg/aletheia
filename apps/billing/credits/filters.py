import django_filters

from apps.billing.credits.models import Credit
from apps.matters.models import Matter
from config.helpers import MultipleOrderingFilter


class CreditsFilter(django_filters.FilterSet):
    matter = django_filters.ModelChoiceFilter(
        queryset=Matter.objects.exclude(status="Closed").order_by("name"),
        empty_label="All",
    )
    date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"})
    )
    order_by = MultipleOrderingFilter(
        fields=[
            (("date", "id"), "date"),
            ("matter__name", "matter"),
            ("detail", "detail"),
        ],
        empty_label=None,
    )

    class Meta:
        model = Credit
        fields = ["matter", "date"]
