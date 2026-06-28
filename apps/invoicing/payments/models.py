from django.db import models
from simple_history.models import HistoricalRecords

from apps.matters.models import Matter
from utils.models import AuditMixin

PAYMENT_METHOD_CHOICES = (
    ("CHECK", "Check"),
    ("CARD", "Card"),
    ("ACH", "ACH / eCheck"),
    ("TRUST", "Trust"),
    ("WIRE", "Wire"),
)


class Payment(AuditMixin, models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE)
    # Payments are client-scoped (a payment can be applied across the client's
    # matters via PaymentApplication). `matter` is being retired in favour of
    # `client`; it is kept nullable through the migration and dropped after.
    client = models.ForeignKey(
        "contacts.Contact", on_delete=models.PROTECT, null=True, blank=True
    )
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    detail = models.CharField(max_length=255, null=True, blank=True)
    # Online-payment provenance (blank for manually-entered payments). Lets the
    # settlement/return webhook find this row and reconcile it.
    processor = models.CharField(max_length=20, blank=True, default="")
    processor_txn_id = models.CharField(
        max_length=64, blank=True, default="", db_index=True
    )
    processor_status = models.CharField(max_length=20, blank=True, default="")
    history = HistoricalRecords()

    def __str__(self):
        return f"Payment #{self.id} - {self.matter}"

    class Meta:
        indexes = [models.Index(fields=["matter"])]
        ordering = ["-date"]
        db_table = "app_invoicing_payment"

    @property
    def method_display(self):
        return dict(PAYMENT_METHOD_CHOICES).get(self.payment_method)

    @property
    def amount_unapplied(self):
        """Calculate the amount of this payment not yet applied to invoices."""
        applied = (
            self.applications.aggregate(models.Sum("amount_applied"))[
                "amount_applied__sum"
            ]
            or 0
        )
        return self.amount - applied

    @property
    def applied_status(self):
        """Return application status: Applied or Unapplied."""
        return "Applied" if self.amount_unapplied == 0 else "Unapplied"
