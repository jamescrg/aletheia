from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.invoicing.unbilled.unbilled import get_unbilled_data


@login_required
def unbilled_index(request):
    """Unbilled view."""
    context = get_unbilled_data(request)

    context = context | {
        "app": "invoicing",
        "subapp": "unbilled",
    }

    return render(request, "invoicing/unbilled/main.html", context)


@login_required
def unbilled_list(request):
    """Unbilled list view for HTMX."""
    context = get_unbilled_data(request)

    return render(request, "invoicing/unbilled/list.html", context)


@login_required
def unbilled_sort(request, order):
    """Handle sorting for unbilled list."""
    filter_data = request.session.get("unbilled_filter", {})

    current_order = filter_data.get("order_by", "")

    # Toggle sort direction if clicking the same column
    if current_order == order:
        new_order = f"-{order}" if not current_order.startswith("-") else order
    else:
        new_order = order

    filter_data["order_by"] = new_order
    request.session["unbilled_filter"] = filter_data
    request.session.modified = True

    return redirect("invoicing:unbilled-list")


@login_required
def unbilled_filter(request):
    """Filter modal for unbilled list."""
    if request.method == "POST":
        filter_data = request.session.get("unbilled_filter", {})
        last_invoice_before = request.POST.get("last_invoice_before", "")
        filter_data["last_invoice_before"] = last_invoice_before
        request.session["unbilled_filter"] = filter_data

        return HttpResponse(status=204, headers={"HX-Trigger": "unbilledListChanged"})

    filter_data = request.session.get("unbilled_filter", {})
    context = {
        "last_invoice_before": filter_data.get("last_invoice_before", ""),
    }
    return render(request, "invoicing/unbilled/filter.html", context)
