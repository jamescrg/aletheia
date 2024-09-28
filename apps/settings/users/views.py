from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.accounts.models import CustomUser


@login_required
def users_index(request):
    users = CustomUser.objects.all()

    page = request.GET.get("page")
    pagination = Paginator(users, 10).get_page(page)

    context = {
        "subapp": "users",
        "users": pagination.object_list,
        "pagination": pagination,
    }

    return render(request, "settings/users/index.html", context)
