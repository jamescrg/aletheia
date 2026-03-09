from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from apps.matters.models import Matter


def matter_access_required(view_func):
    """Decorator for views with a matter id param. Checks user has access."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        matter_id = kwargs.get("id") or kwargs.get("matter_id")
        if matter_id:
            matter = get_object_or_404(Matter, pk=matter_id)
            if not request.user.has_matter_access(matter):
                return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    return wrapper


def filter_matters_for_user(queryset, user):
    """If user lacks perm_all_matters, filter to assigned_matters."""
    if user.is_admin or user.perm_all_matters:
        return queryset
    return queryset.filter(members=user)
