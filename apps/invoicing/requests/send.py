"""Send a payment request: email the catch-up pay link + the matter ledger
statement to the client. Mirrors apps.invoicing.invoices.functions.send_invoice.
"""

import os

from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import timezone

from apps.invoicing.pay.links import request_pay_url
from apps.matters.ledger.generate_ledger import generate_ledger
from apps.settings.models import Company
from utils.mail import render_inlined


class PaymentRequestSendError(Exception):
    pass


def _parse_recipients(raw):
    """Split a comma/semicolon-delimited address string into a clean list."""
    if not raw:
        return []
    return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]


def _invalid_addresses(addresses):
    invalid = []
    for addr in addresses:
        try:
            validate_email(addr)
        except ValidationError:
            invalid.append(addr)
    return invalid


def send_payment_request(
    payment_request, *, to=None, cc=None, message=None, request=None
):
    """Email the request's pay link + the matter ledger statement PDF.

    to / cc: comma-delimited address strings; `to` defaults to the request's
    stored recipient(s). message: optional cover note. Returns True; raises
    PaymentRequestSendError on a bad/empty address list or send failure.
    """
    matter = payment_request.matter
    client = matter.client if matter else None

    to_list = _parse_recipients(to) or _parse_recipients(
        payment_request.recipient_email
    )
    cc_list = _parse_recipients(cc)
    if not to_list:
        raise PaymentRequestSendError("Enter at least one recipient email address.")
    invalid = _invalid_addresses(to_list + cc_list)
    if invalid:
        raise PaymentRequestSendError(
            f"Invalid email address(es): {', '.join(invalid)}"
        )

    company = Company.objects.first()
    bcc_list = (
        [a.strip() for a in (company.invoice_bcc or "").split(",") if a.strip()]
        if company
        else []
    )
    context = {
        "matter_name": matter.name if matter else "",
        "matter_number": matter.id if matter else "",
        "client_name": client.name if client else "",
        "amount_due": payment_request.amount_requested,
        "cover_message": message or "",
        "firm_name": company.name if company else "",
        "firm_email": company.email if company else "",
        "pay_url": request_pay_url(payment_request, request),
    }
    firm = company.name if company else ""
    subject = f"{firm} - " if firm else ""
    subject += "Payment request"
    if matter:
        subject += f" - Matter {matter.id}"

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=render_to_string("emails/payment_request_email.txt", context),
            from_email=None,  # falls back to DEFAULT_FROM_EMAIL
            to=to_list,
            cc=cc_list or None,
            bcc=bcc_list or None,
            reply_to=[company.email] if company and company.email else None,
        )
        email.attach_alternative(
            render_inlined("emails/payment_request_email.html", context), "text/html"
        )
        # Attach the matter ledger statement (current account activity + balance).
        pdf_tmp = generate_ledger(matter.id, request)
        filename = f"Matter Ledger {matter.id} {timezone.localdate():%Y-%m-%d}.pdf"
        try:
            with open(pdf_tmp.name, "rb") as f:
                email.attach(filename, f.read(), "application/pdf")
        finally:
            os.unlink(pdf_tmp.name)
        email.send()
    except PaymentRequestSendError:
        raise
    except Exception as exc:
        raise PaymentRequestSendError(
            f"Could not send the payment request: {exc}"
        ) from exc
    return True
