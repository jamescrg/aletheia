import django_filters
from django.db.models import Q

from apps.case.models import Label
from apps.notes.models import Note
from config.helpers import MultipleOrderingFilter

IMPORTANCE_CHOICES = (
    (7, "Highest"),
    (6, "Higher"),
    (5, "High"),
    (4, "Normal"),
    (3, "Low"),
    (2, "Lower"),
    (1, "Lowest"),
)

SOURCE_CHOICES = (
    ("synced", "Synced from Drive"),
    ("manual", "Created in app"),
)


class NotesFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(method="filter_keyword", label="Keyword")
    label = django_filters.ModelChoiceFilter(
        method="filter_label",
        queryset=Label.objects.none(),
        empty_label="All Labels",
        label="Label",
    )
    category = django_filters.ChoiceFilter(
        field_name="category",
        choices=Note.CATEGORY_CHOICES,
        label="Category",
        empty_label="All Categories",
    )
    topic = django_filters.CharFilter(field_name="topic", lookup_expr="exact")
    source = django_filters.ChoiceFilter(
        method="filter_source",
        choices=SOURCE_CHOICES,
        label="Source",
        empty_label="All Sources",
    )
    importance = django_filters.ChoiceFilter(
        field_name="importance",
        choices=IMPORTANCE_CHOICES,
        lookup_expr="gte",
        label="Importance (≥)",
        empty_label="All",
    )
    order_by = MultipleOrderingFilter(
        fields=[
            ("updated_at", "updated_at"),
            ("created_at", "created_at"),
            ("title", "title"),
            ("topic", "topic"),
            ("importance", "importance"),
            ("viewed_at", "viewed_at"),
        ],
        field_labels={
            "updated_at": "Last Updated",
            "created_at": "Created",
            "title": "Title",
            "topic": "Topic",
            "importance": "Importance",
            "viewed_at": "Viewed",
        },
        label="Order By",
    )

    class Meta:
        model = Note
        fields = ["keyword", "label", "category", "importance", "source", "order_by"]

    def __init__(self, *args, matter=None, **kwargs):
        super().__init__(*args, **kwargs)
        if matter:
            self.filters["label"].queryset = Label.objects.filter(
                Q(matter=matter) | Q(matter__isnull=True)
            ).order_by("name")

    def filter_keyword(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) | Q(content__icontains=value)
            )
        return queryset

    def filter_label(self, queryset, name, value):
        if value:
            return queryset.filter(labels=value)
        return queryset

    def filter_source(self, queryset, name, value):
        if value == "synced":
            return queryset.filter(drive_file_id__isnull=False)
        if value == "manual":
            return queryset.filter(drive_file_id__isnull=True)
        return queryset
