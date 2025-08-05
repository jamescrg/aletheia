import django_filters

from apps.intakes.models import Intake

INTAKE_STATUS_CHOICES = (
    ("Open", "Open"),
    ("Accepted", "Accepted"),
    ("Pending", "Pending"),
    ("Referred Out", "Referred Out"),
    ("Client Declined", "Client Declined"),
    ("Unresponsive", "Unresponsive"),
)

PRACTICE_AREA_CHOICES = (
    ("General", "General"),
    ("Boundary", "Boundary"),
    ("Title", "Title"),
    ("LLT - LL", "LLT - LL"),
    ("LLT - T", "LLT - T"),
    ("QT", "QT"),
    ("HOA", "HOA"),
    ("Fraud", "Fraud"),
    ("Construction", "Construction"),
)

SOURCE_CHOICES = (
    ("Unknown", "Unknown"),
    ("Internet", "Internet"),
    ("Agent", "Agent"),
    ("Attorney - Internal", "Attorney - Internal"),
    ("Attorney - External", "Attorney - External"),
    ("Other", "Other"),
)


class IntakeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=INTAKE_STATUS_CHOICES, empty_label="All"
    )
    practice_area = django_filters.ChoiceFilter(
        choices=PRACTICE_AREA_CHOICES, empty_label="All"
    )
    date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"type": "date"})
    )
    source = django_filters.ChoiceFilter(choices=SOURCE_CHOICES, empty_label="All")
    order_by = django_filters.OrderingFilter(
        fields=(
            ("date", "date"),
            ("name", "name"),
        ),
        field_labels={
            "date": "Date",
            "name": "Name",
        },
        empty_label=None,
    )

    class Meta:
        model = Intake
        fields = ["status", "practice_area", "date"]
