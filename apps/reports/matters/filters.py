import django_filters

from apps.matters.models import Matter


class MatterSummaryFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = Matter
        fields = ["status"]
