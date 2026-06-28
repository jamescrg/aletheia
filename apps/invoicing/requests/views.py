from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.invoicing.pay.balance import matter_balance_cents
from apps.invoicing.requests.filters import PaymentRequestFilter
from apps.invoicing.requests.models import PaymentRequest
from apps.invoicing.requests.send import (
    PaymentRequestSendError,
    send_payment_request,
)
from apps.management.pagination import CustomPaginator
from apps.matters.models import Matter
from utils.toasts import toast_success

# Filter keys that don't count toward the "filter is active" toolbar highlight:
# status has its own quick-buttons, and the POST carries the CSRF token.
_NON_FILTER_KEYS = ("status", "order_by", "csrfmiddlewaretoken")


def _requests_context(request):
    filter_data = request.session.get("requests_filter", {})
    base = PaymentRequest.objects.select_related("matter", "payment").order_by(
        "-created_at"
    )
    requests = (
        PaymentRequestFilter(filter_data, queryset=base).qs if filter_data else base
    )
    pagination = CustomPaginator(
        requests, per_page=10, request=request, session_key="requests_pagination"
    )
    filter_active = bool(
        filter_data
        and any(
            v
            for k, v in filter_data.items()
            if k not in _NON_FILTER_KEYS and v not in (None, "")
        )
    )
    return {
        "app": "invoicing",
        "subapp": "requests",
        "pagination": pagination,
        "session_key": "requests_pagination",
        "trigger_key": "requestsChanged",
        "objects": pagination.get_object_list(),
        "current_status": filter_data.get("status", ""),
        "filter_active": filter_active,
    }


@login_required
def requests_index(request):
    return render(request, "invoicing/requests/main.html", _requests_context(request))


@login_required
def requests_list(request):
    return render(request, "invoicing/requests/list.html", _requests_context(request))


@login_required
def requests_filter(request):
    """Filter modal: matter / date / status. POST stores the cleaned filter in
    the session; GET renders the modal bound to the current filter."""
    if request.method == "POST":
        request.session["requests_filter"] = {
            k: v for k, v in request.POST.items() if k != "csrfmiddlewaretoken"
        }
        return HttpResponse(status=204, headers={"HX-Trigger": "requestsChanged"})
    filter_data = request.session.get("requests_filter")
    base = PaymentRequest.objects.select_related("matter").order_by("-created_at")
    payment_request_filter = PaymentRequestFilter(filter_data or None, queryset=base)
    return render(
        request, "invoicing/requests/filter.html", {"filter": payment_request_filter}
    )


@login_required
def requests_filter_status(request, status):
    """Quick status filter (Sent / Paid / Canceled). Toggling the active one or
    passing 'all' clears it. Shares the session filter dict with the modal."""
    filter_data = dict(request.session.get("requests_filter", {}))
    if status == "all" or filter_data.get("status") == status:
        filter_data.pop("status", None)
    else:
        filter_data["status"] = status
    request.session["requests_filter"] = filter_data
    request.session.modified = True
    return HttpResponse(status=204, headers={"HX-Trigger": "requestsChanged"})


def _open_matters():
    return Matter.objects.exclude(status__in=["Pending", "Closed"]).order_by("name")


@login_required
def requests_new(request):
    """Create + send a payment request for a matter's full open balance."""
    if request.method == "POST":
        matter_id = request.POST.get("matter") or ""
        to = (request.POST.get("to") or "").strip()
        cc = (request.POST.get("cc") or "").strip()
        message = request.POST.get("message", "")
        matter = _open_matters().filter(pk=matter_id).first() if matter_id else None

        error = ""
        balance_cents = 0
        if not matter:
            error = "Please select a matter."
        else:
            balance_cents = matter_balance_cents(matter)
            if balance_cents <= 0:
                error = "This matter has no open balance to request."

        if not error:
            payment_request = PaymentRequest(
                matter=matter,
                amount_requested=Decimal(balance_cents) / 100,
                recipient_email=to,
                status="SENT",
            )
            # Persist + send together: if the email fails (incl. validation),
            # roll back so we never leave an unsent request behind.
            try:
                with transaction.atomic():
                    payment_request.save()
                    send_payment_request(
                        payment_request, to=to, cc=cc, message=message, request=request
                    )
            except PaymentRequestSendError as exc:
                error = str(exc)
            else:
                response = HttpResponse(
                    status=204, headers={"HX-Trigger": "requestsChanged"}
                )
                toast_success(response, f"Payment request sent to {to}.")
                return response

        context = {
            "matters": _open_matters(),
            "matter_id": matter_id,
            "to": to,
            "cc": cc,
            "message": message,
            "error": error,
        }
        return render(request, "invoicing/requests/form.html", context)

    context = {
        "matters": _open_matters(),
        "matter_id": "",
        "to": "",
        "cc": "",
        "message": "",
        "error": "",
    }
    return render(request, "invoicing/requests/form.html", context)


@login_required
def requests_matter_email(request):
    """Return the To input pre-filled with the selected matter's client email —
    htmx swaps it in when the matter dropdown changes."""
    matter_id = request.GET.get("matter")
    email = ""
    if matter_id:
        matter = Matter.objects.filter(pk=matter_id).select_related("client").first()
        if matter and matter.client:
            email = matter.client.email or ""
    return render(request, "invoicing/requests/to_input.html", {"to": email})


@login_required
def requests_cancel(request, pk):
    payment_request = get_object_or_404(PaymentRequest, pk=pk)
    if payment_request.status == "SENT":
        payment_request.status = "CANCELED"
        payment_request.save(update_fields=["status"])
    return render(
        request, "invoicing/requests/row.html", {"payment_request": payment_request}
    )
