"""Public, no-login invoice payment page.

The client opens a tokenized link (`/pay/<signed-token>/`), sees the invoice
summary, enters card or bank details into the active processor's hosted fields
(which tokenize client-side — card/bank data never reaches us), and submits the
one-time token to `pay_charge`, which charges it via the configured processor.

This is the app's only record-exposing public surface, so access is gated by the
signed, expiring token (see `utils.signing`), not a session.

NOTE (Piece 3): recording the resulting Payment + applying it to the invoice,
the settlement/return webhook, and rate-limiting live in the next piece. Today
the charge is performed and its result reported; the invoice is not yet updated.
"""

import json

from django.conf import settings
from django.core import signing
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.invoicing.invoices.models import Invoice
from apps.invoicing.processors import ChargeError, get_processor
from utils.signing import read_payment_token


def _resolve_invoice(token):
    """Return the invoice for a signed token, or raise Http404 with a reason
    suitable for the 'link unavailable' page."""
    try:
        invoice_uuid = read_payment_token(
            token, max_age=settings.INVOICE_PAY_LINK_MAX_AGE
        )
    except signing.SignatureExpired:
        raise Http404("expired")
    except signing.BadSignature:
        raise Http404("invalid")
    return get_object_or_404(Invoice, uuid=invoice_uuid)


def _unavailable(request, reason, *, status):
    return render(
        request, "invoicing/pay/unavailable.html", {"reason": reason}, status=status
    )


def pay_page(request, token):
    try:
        invoice = _resolve_invoice(token)
    except Http404 as exc:
        reason = str(exc)
        if reason == "expired":
            return _unavailable(
                request,
                "This payment link has expired. Please contact us for a new one.",
                status=410,
            )
        return _unavailable(request, "This payment link is invalid.", status=404)

    processor = get_processor()
    config = processor.client_config(invoice)
    matter = invoice.matter
    context = {
        "invoice": invoice,
        "matter_name": matter.name if matter else "",
        "firm_name": getattr(settings, "FIRM_NAME", ""),
        "amount_due": invoice.amount_remaining,
        "config": config,
        "is_paid": invoice.amount_remaining <= 0,
        # Dev/fake processor: render a simulated-outcome form instead of the
        # real hosted-fields SDK so the whole flow is testable without LawPay.
        "dev_mode": config.processor == "fake",
        "charge_url": request.build_absolute_uri(request.path.rstrip("/") + "/charge/"),
    }
    return render(request, "invoicing/pay/pay.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def pay_charge(request, token):
    # Token gates access in lieu of a session; an invalid/expired token 404s.
    invoice = _resolve_invoice(token)

    try:
        body = json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return JsonResponse(
            {"success": False, "error": "Malformed request."}, status=400
        )

    payment_token = (body.get("token") or "").strip()
    method = body.get("method") or ""
    if not payment_token:
        return JsonResponse(
            {"success": False, "error": "Missing payment details."}, status=400
        )

    processor = get_processor()
    config = processor.client_config(invoice)
    if config.amount_cents <= 0:
        return JsonResponse(
            {"success": False, "error": "This invoice is already paid."}, status=400
        )

    try:
        result = processor.charge(
            token=payment_token,
            amount_cents=config.amount_cents,
            reference=config.reference,
            method=method,
            idempotency_key=config.reference,
        )
    except ChargeError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=402)

    # Piece 3 records a Payment + applies it (provisional for pending ACH) and
    # the webhook confirms/reverses. For now report the processor result.
    pending = result.status == "pending"
    return JsonResponse(
        {
            "success": True,
            "pending": pending,
            "status": result.status,
            "transaction_id": result.transaction_id,
        }
    )
