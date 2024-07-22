from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.invoicing.models import Invoice


@login_required
def index(request):
    invoices = (
        Invoice.objects.all()
        .select_related("matter", "created_by")
        .order_by("-created_at")
    )

    context = {
        "page": "invoicing",
        "invoices": invoices,
    }

    return render(request, "invoicing/list.html", context)
