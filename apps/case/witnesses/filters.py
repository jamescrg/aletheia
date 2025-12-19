import django_filters
from django.db.models import Q

from apps.case.models import Witness
from config.helpers import MultipleOrderingFilter

IMPORTANCE_CHOICES = tuple((i, f"Importance {i}") for i in range(1, 11))

ALIGNMENT_CHOICES = [
    ("friendly", "Friendly"),
    ("neutral", "Neutral"),
    ("hostile", "Hostile"),
]


class WitnessesFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(method="filter_keyword", label="Keyword")
    alignment = django_filters.ChoiceFilter(
        field_name="alignment",
        choices=ALIGNMENT_CHOICES,
        label="Alignment",
        empty_label="All",
    )
    importance = django_filters.ChoiceFilter(
        field_name="importance",
        choices=IMPORTANCE_CHOICES,
        lookup_expr="lte",
        label="Importance (≤)",
        empty_label="All",
    )
    order_by = MultipleOrderingFilter(
        fields=[
            ("name", "name"),
            ("affiliation", "affiliation"),
            ("alignment", "alignment"),
            ("importance", "importance"),
        ],
        field_labels={
            "name": "Name",
            "affiliation": "Affiliation",
            "alignment": "Alignment",
            "importance": "Importance",
        },
        label="Order By",
    )

    class Meta:
        model = Witness
        fields = [
            "keyword",
            "alignment",
            "importance",
            "order_by",
        ]

    def filter_keyword(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(knowledge__icontains=value)
            )
        return queryset
