from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.matters.models import Matter


@login_required
def collections_list(request):
    matters = Matter.objects.filter(status__in=["Open", "Complete"]).order_by("name")

    page = request.GET.get("page")
    pagination = Paginator(matters, 10).get_page(page)

    context = {
        "app": "billing",
        "subapp": "collections",
        "matters": pagination.object_list,
        "pagination": pagination,
    }

    return render(request, "billing/collections/list.html", context)
