from apps.matters.models import Relationship


def load_contacts(matter):
    """
    Returns a queryset of relationships with group included.
    """
    return (
        Relationship.objects.select_related("contact", "role", "group")
        .filter(matter=matter)
        .order_by("group__order", "contact__name")
    )
