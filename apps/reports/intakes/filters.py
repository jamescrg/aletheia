import django_filters

from apps.intakes.models import Intake


class IntakeReportFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Intake
        fields = ["date_from", "date_to"]
