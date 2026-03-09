from django import template

from apps.accounts.access import filter_matters_for_user
from apps.matters.models import Matter

register = template.Library()


@register.simple_tag(takes_context=True)
def get_open_matters(context):
    matters = Matter.objects.filter(status="Open").order_by("name")
    request = context.get("request")
    if request and hasattr(request, "user") and request.user.is_authenticated:
        matters = filter_matters_for_user(matters, request.user)
    return matters
