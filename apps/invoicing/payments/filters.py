import django_filters

from apps.invoicing.payments.models import PAYMENT_METHOD_CHOICES, Payment
from apps.matters.models import Matter
from config.helpers import MultipleOrderingFilter


class PaymentFilter(django_filters.FilterSet):
    payment_method = django_filters.ChoiceFilter(
        choices=PAYMENT_METHOD_CHOICES, empty_label="All"
    )
    matter = django_filters.ModelChoiceFilter(
        queryset=Matter.objects.exclude(status__in=["Pending", "Closed"]).order_by(
            "name"
        ),
        empty_label="All",
    )
    applied_status = django_filters.ChoiceFilter(
        choices=[
            ("applied", "Applied"),
            ("unapplied", "Unapplied"),
        ],
        method="filter_applied_status",
        empty_label="All",
        label="Application Status",
    )
    date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"})
    )
    order_by = MultipleOrderingFilter(
        fields=[
            (("date", "id"), "date"),
            ("matter__name", "matter"),
            ("payment_method", "payment_method"),
            ("detail", "detail"),
        ],
        empty_label=None,
    )

    def filter_applied_status(self, queryset, name, value):
        """Filter payments by application status."""

        if value == "applied":
            # Find payments where applied amount equals payment amount
            payment_ids = []
            for payment in queryset:
                if payment.amount_unapplied == 0:
                    payment_ids.append(payment.id)
            return queryset.filter(id__in=payment_ids)
        elif value == "unapplied":
            # Find payments with any unapplied amount
            payment_ids = []
            for payment in queryset:
                if payment.amount_unapplied > 0:
                    payment_ids.append(payment.id)
            return queryset.filter(id__in=payment_ids)
        return queryset

    class Meta:
        model = Payment
        fields = ["payment_method", "matter", "date", "applied_status"]
