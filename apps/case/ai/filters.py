import django_filters

from .models import Conversation


class ConversationFilter(django_filters.FilterSet):
    order_by = django_filters.OrderingFilter(
        fields=[
            ("title", "title"),
            ("created_at", "created_at"),
            ("last_activity", "last_activity"),
        ],
        label="Order By",
    )

    class Meta:
        model = Conversation
        fields = ["order_by"]
