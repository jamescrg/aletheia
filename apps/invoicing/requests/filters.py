import django_filters

from apps.invoicing.requests.models import STATUS_CHOICES, PaymentRequest
from apps.matters.models import Matter


class PaymentRequestFilter(django_filters.FilterSet):
    matter = django_filters.ModelChoiceFilter(
        queryset=Matter.objects.exclude(status__in=["Pending", "Closed"]).order_by(
            "name"
        ),
        empty_label="All",
    )
    status = django_filters.ChoiceFilter(choices=STATUS_CHOICES, empty_label="All")
    date = django_filters.DateFromToRangeFilter(
        field_name="created_at",
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"}),
        label="Date",
    )

    class Meta:
        model = PaymentRequest
        fields = ["matter", "status", "date"]
