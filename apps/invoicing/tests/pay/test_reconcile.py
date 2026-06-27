"""Tests for the settlement/return reconciliation path.

The critical, previously-untested behaviour: an accepted ACH charge that later
**returns** must be unapplied, the invoice reverted from PAID to SENT, the
phantom Payment removed, and staff emailed.

We drive a charge through the FakeProcessor (so its txn lives in the registry),
record it with ``record_payment``, then feed a webhook body to
``reconcile_webhook``. The fake's webhook parser honours a ``status`` in the body
and reports it back as the confirmed status (mirroring "re-fetch to confirm").
"""

import json

import pytest

from apps.invoicing.applications.models import PaymentApplication
from apps.invoicing.invoices.models import Invoice
from apps.invoicing.pay.reconcile import reconcile_webhook
from apps.invoicing.pay.recording import record_payment
from apps.invoicing.payments.models import Payment
from apps.invoicing.processors import BANK, CARD, get_processor

pytestmark = pytest.mark.django_db


def _charge_and_record(invoice, *, token, method):
    """Charge via the fake processor (populating its registry) and record the
    resulting Payment applied to ``invoice``. Returns (payment, result)."""
    processor = get_processor()
    config = processor.client_config(invoice)
    result = processor.charge(
        token=token,
        amount_cents=config.amount_cents,
        reference=config.reference,
        method=method,
    )
    payment = record_payment(invoice, result)
    return payment, result


def _webhook_body(txn_id, status):
    return json.dumps({"transaction_id": txn_id, "status": status})


# ---------------------------------------------------------------------------
# record_payment
# ---------------------------------------------------------------------------
class TestRecordPayment:
    def test_records_and_applies(self, sent_invoice):
        payment, result = _charge_and_record(sent_invoice, token="fake-ok", method=CARD)
        assert payment is not None
        assert PaymentApplication.objects.filter(
            payment=payment, invoice=sent_invoice
        ).exists()
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"

    def test_idempotent_on_same_transaction(self, sent_invoice):
        payment, result = _charge_and_record(sent_invoice, token="fake-ok", method=CARD)
        again = record_payment(sent_invoice, result)
        assert again.pk == payment.pk
        assert Payment.objects.filter(processor="fake").count() == 1

    def test_returns_none_without_matter(self, user):
        """Payment requires a matter; a matter-less invoice cannot be recorded."""
        invoice = Invoice.objects.create(
            created_by=user,
            matter=None,
            date_limit="2024-12-31",
            date_issued="2024-12-01",
            status="SENT",
        )
        processor = get_processor()
        result = processor.charge(
            token="fake-ok",
            amount_cents=10000,
            reference="invoice:x",
            method=CARD,
        )
        assert record_payment(invoice, result) is None


# ---------------------------------------------------------------------------
# reconcile_webhook — the ACH return reversal
# ---------------------------------------------------------------------------
class TestReversal:
    def test_returned_event_reverses_payment(self, sent_invoice, settings, mailoutbox):
        settings.ADMINS = [("Admin", "admin@example.test")]

        payment, result = _charge_and_record(
            sent_invoice, token="fake-ach-return", method=BANK
        )
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"  # provisional

        reconcile_webhook("fake", _webhook_body(result.transaction_id, "returned"))

        # Payment + application removed.
        assert not Payment.objects.filter(pk=payment.pk).exists()
        assert not PaymentApplication.objects.filter(payment=payment).exists()

        # Invoice reverted to unpaid.
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "SENT"
        assert sent_invoice.amount_remaining > 0

        # Staff notified.
        assert len(mailoutbox) == 1
        assert "returned" in mailoutbox[0].subject.lower()
        assert result.transaction_id in mailoutbox[0].subject

    def test_failed_event_also_reverses(self, sent_invoice, settings, mailoutbox):
        settings.ADMINS = [("Admin", "admin@example.test")]
        payment, result = _charge_and_record(
            sent_invoice, token="fake-ach-fail", method=BANK
        )
        reconcile_webhook("fake", _webhook_body(result.transaction_id, "failed"))

        assert not Payment.objects.filter(pk=payment.pk).exists()
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "SENT"
        assert len(mailoutbox) == 1


# ---------------------------------------------------------------------------
# reconcile_webhook — non-reversing + idempotency + safety
# ---------------------------------------------------------------------------
class TestNonReversingAndIdempotent:
    def test_pending_to_succeeded_updates_status_without_unapplying(
        self, sent_invoice, mailoutbox
    ):
        payment, result = _charge_and_record(sent_invoice, token="fake-ok", method=BANK)
        assert payment.processor_status == "pending"

        reconcile_webhook("fake", _webhook_body(result.transaction_id, "succeeded"))

        payment.refresh_from_db()
        assert payment.processor_status == "succeeded"
        # Still applied; invoice still paid; no reversal email.
        assert PaymentApplication.objects.filter(payment=payment).exists()
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"
        assert len(mailoutbox) == 0

    def test_idempotent_redelivery_is_noop(self, sent_invoice, mailoutbox):
        payment, result = _charge_and_record(sent_invoice, token="fake-ok", method=CARD)
        assert payment.processor_status == "succeeded"

        # Same status re-delivered — nothing changes, no email.
        reconcile_webhook("fake", _webhook_body(result.transaction_id, "succeeded"))

        assert Payment.objects.filter(pk=payment.pk).exists()
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"
        assert len(mailoutbox) == 0

    def test_event_for_already_reversed_payment_is_noop(
        self, sent_invoice, settings, mailoutbox
    ):
        settings.ADMINS = [("Admin", "admin@example.test")]
        payment, result = _charge_and_record(
            sent_invoice, token="fake-ach-return", method=BANK
        )
        # First return reverses it (1 email).
        reconcile_webhook("fake", _webhook_body(result.transaction_id, "returned"))
        assert not Payment.objects.filter(pk=payment.pk).exists()
        assert len(mailoutbox) == 1

        # A duplicate return for the now-removed payment is a safe no-op.
        reconcile_webhook("fake", _webhook_body(result.transaction_id, "returned"))
        assert len(mailoutbox) == 1

    def test_event_for_unknown_transaction_is_safe(self, mailoutbox):
        """A webhook for a transaction we never recorded (and isn't even in the
        registry) is swallowed without error and changes nothing."""
        reconcile_webhook("fake", _webhook_body("fake_card_doesnotexist", "returned"))
        assert len(mailoutbox) == 0

    def test_unknown_processor_is_ignored(self, mailoutbox):
        reconcile_webhook("nope", _webhook_body("whatever", "returned"))
        assert len(mailoutbox) == 0
