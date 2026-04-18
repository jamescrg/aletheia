import django_filters
from django.db.models import Q

from apps.case.models import Document, Highlight, Label

IMPORTANCE_CHOICES = (
    (7, "Highest"),
    (6, "Higher"),
    (5, "High"),
    (4, "Normal"),
    (3, "Low"),
    (2, "Lower"),
    (1, "Lowest"),
)

SOURCE_TYPE_CHOICES = [
    ("", "All Sources"),
    ("case", "Cases"),
    ("document", "Documents"),
]


class HighlightsFilter(django_filters.FilterSet):
    """Filter for highlights list."""

    source_type = django_filters.ChoiceFilter(
        method="filter_source_type",
        choices=SOURCE_TYPE_CHOICES,
        label="Source Type",
        empty_label=None,
    )
    document = django_filters.ModelChoiceFilter(
        queryset=Document.objects.none(),
        empty_label="All",
        label="Document",
    )
    keyword = django_filters.CharFilter(method="filter_keyword", label="Keyword")
    label = django_filters.ModelChoiceFilter(
        method="filter_label",
        queryset=Label.objects.none(),
        empty_label="All Labels",
        label="Label",
    )
    importance = django_filters.ChoiceFilter(
        field_name="importance",
        choices=IMPORTANCE_CHOICES,
        lookup_expr="gte",
        label="Importance (≥)",
        empty_label="All",
    )
    order_by = django_filters.OrderingFilter(
        fields=[
            ("created_at", "created"),
            ("document__date", "date"),
            ("document__name", "document"),
            ("slug", "slug"),
            ("importance", "importance"),
        ],
        field_labels={
            "created_at": "Created",
            "document__date": "Date",
            "document__name": "Document",
            "slug": "Slug",
            "importance": "Importance",
        },
        label="Order By",
    )

    class Meta:
        model = Highlight
        fields = [
            "source_type",
            "document",
            "keyword",
            "label",
            "importance",
            "order_by",
        ]

    def __init__(self, *args, matter=None, **kwargs):
        super().__init__(*args, **kwargs)
        if matter:
            self.filters["document"].queryset = Document.objects.filter(
                matter=matter
            ).order_by("name")
            self.filters["label"].queryset = Label.objects.filter(
                Q(matter=matter) | Q(matter__isnull=True)
            ).order_by("name")

    def filter_keyword(self, queryset, name, value):
        """Filter highlights by keyword in slug or text."""
        if value:
            return queryset.filter(Q(slug__icontains=value) | Q(text__icontains=value))
        return queryset

    def filter_label(self, queryset, name, value):
        """Filter highlights by label."""
        if value:
            return queryset.filter(labels=value)
        return queryset

    def filter_source_type(self, queryset, name, value):
        """Filter highlights by source type (case or document)."""
        if value == "case":
            return queryset.filter(caselaw__isnull=False)
        elif value == "document":
            return queryset.filter(document__isnull=False)
        return queryset
