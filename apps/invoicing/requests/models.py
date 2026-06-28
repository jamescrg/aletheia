"""A payment request: an outgoing ask for a matter's full open balance.

Distinct from a Payment, which only exists once money moves. A request is created
(status SENT) when the firm emails a client a catch-up balance link; it flips to
PAID when that link is paid (see apps.invoicing.pay), recording the resulting
Payment. The signed pay-link token carries this row's ``uuid`` (never its pk).
"""

import uuid

from django.db import models
from simple_history.models import HistoricalRecords

from apps.invoicing.payments.models import Payment
from apps.matters.models import Matter
from utils.models import AuditMixin

STATUS_CHOICES = (
    ("SENT", "Sent"),
    ("PAID", "Paid"),
    ("CANCELED", "Canceled"),
)


class PaymentRequest(AuditMixin, models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    matter = models.ForeignKey(
        Matter, on_delete=models.CASCADE, related_name="payment_requests"
    )
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_email = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="SENT")
    # Set when this request's link is paid; SET_NULL keeps the request's record
    # even if the payment row is later removed.
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"Payment request #{self.id} - {self.matter}"

    class Meta:
        db_table = "app_invoicing_payment_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["matter"]),
        ]
