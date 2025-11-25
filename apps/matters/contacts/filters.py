import django_filters

from apps.matters.models import Group, Relationship, Role


class MatterContactFilter(django_filters.FilterSet):
    group = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        label="Group",
        empty_label="All",
    )
    role = django_filters.ModelChoiceFilter(
        queryset=Role.objects.all().order_by("name"),
        label="Role",
        empty_label="All",
    )
    order_by = django_filters.OrderingFilter(
        fields=(
            ("group__order", "group"),
            ("role__name", "role"),
            ("contact__name", "name"),
        ),
    )

    class Meta:
        model = Relationship
        fields = ["group", "role"]
