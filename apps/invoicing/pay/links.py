"""Build public payment links for an invoice."""

from django.conf import settings
from django.urls import reverse

from utils.signing import make_payment_token


def payment_path(invoice) -> str:
    """Root-relative payment URL, e.g. /pay/<signed-token>/."""
    return reverse("pay:invoice", kwargs={"token": make_payment_token(invoice)})


def payment_url(invoice, request=None) -> str:
    """Absolute payment URL for emails / off-request contexts.

    Uses the request host when available, else settings.PUBLIC_BASE_URL.
    """
    path = payment_path(invoice)
    if request is not None:
        return request.build_absolute_uri(path)
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    return f"{base}{path}" if base else path
