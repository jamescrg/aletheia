from django.db import models

from apps.accounts.models import CustomUser
from apps.matters.models import Matter

INVOICE_STATUS = (
    ("DRAFT", "Draft"),
    ("SENT", "Sent"),
    ("CANCELLED", "Cancelled"),
    ("APPROVED", "Approved"),
)


class Invoice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    matter = models.ForeignKey(Matter, on_delete=models.SET_NULL, null=True, blank=True)
    date_from = models.DateField()
    date_to = models.DateField()
    issue_date = models.DateField()
    message = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    show_comp = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default="DRAFT")
    approved_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invoice #{self.id}"

    class Meta:
        indexes = [models.Index(fields=["matter"])]

    @property
    def amount(self):
        return 3000
