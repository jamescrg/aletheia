"""End-to-end tests for the public ``pay_charge`` view.

The view is csrf_exempt and gated only by a signed payment token, so we mint a
real token with ``make_payment_token`` and POST JSON to the charge URL via the
Django test client. Everything is charged through the FakeProcessor.
"""

import json
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.invoicing.payments.models import Payment
from apps.invoicing.processors import BANK, CARD
from utils.signing import make_payment_token

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_client():
    """A plain (unauthenticated) client — the pay page is a public surface."""
    return Client()


def _charge_url(invoice):
    return reverse("pay:charge", kwargs={"token": make_payment_token(invoice)})


def _post_charge(client, invoice, *, token="fake-ok", method=CARD, body=None):
    url = _charge_url(invoice)
    if body is None:
        body = {"token": token, "method": method}
    return client.post(url, data=json.dumps(body), content_type="application/json")


class TestPayChargeHappyPath:
    def test_card_charge_records_payment_and_pays_invoice(
        self, public_client, sent_invoice
    ):
        response = _post_charge(public_client, sent_invoice, method=CARD)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pending"] is False
        assert data["status"] == "succeeded"
        assert data["transaction_id"]

        # A Payment was recorded with processor provenance.
        payment = Payment.objects.get(processor="fake")
        assert payment.processor_txn_id == data["transaction_id"]
        assert payment.processor_status == "succeeded"
        assert payment.payment_method == "CARD"
        assert payment.amount == Decimal("1000.00")

        # Invoice flipped to PAID via the PaymentApplication hook.
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"
        assert sent_invoice.amount_remaining == 0

    def test_pending_ach_charge_records_payment_and_reports_pending(
        self, public_client, sent_invoice
    ):
        response = _post_charge(public_client, sent_invoice, method=BANK)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pending"] is True
        assert data["status"] == "pending"

        payment = Payment.objects.get(processor="fake")
        assert payment.payment_method == "ACH"
        assert payment.processor_status == "pending"

        # Provisional PAID: the invoice shows paid even though ACH is in flight.
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "PAID"


class TestPayChargeFailures:
    def test_decline_returns_402_and_records_nothing(self, public_client, sent_invoice):
        response = _post_charge(public_client, sent_invoice, token="fake-decline")
        assert response.status_code == 402
        assert response.json()["success"] is False

        assert not Payment.objects.exists()
        sent_invoice.refresh_from_db()
        assert sent_invoice.status == "SENT"

    def test_already_paid_invoice_returns_400_no_charge(
        self, public_client, paid_invoice
    ):
        response = _post_charge(public_client, paid_invoice, method=CARD)
        assert response.status_code == 400
        assert response.json()["success"] is False
        # No online payment recorded for an already-settled invoice.
        assert not Payment.objects.filter(processor="fake").exists()

    def test_missing_token_returns_400(self, public_client, sent_invoice):
        response = _post_charge(public_client, sent_invoice, body={"method": CARD})
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert not Payment.objects.exists()

    def test_malformed_json_returns_400(self, public_client, sent_invoice):
        response = public_client.post(
            _charge_url(sent_invoice),
            data="not-json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert not Payment.objects.exists()

    def test_invalid_token_404s(self, public_client, sent_invoice):
        url = reverse("pay:charge", kwargs={"token": "tampered-token"})
        response = public_client.post(
            url,
            data=json.dumps({"token": "fake-ok", "method": CARD}),
            content_type="application/json",
        )
        assert response.status_code == 404


class TestPayChargeLocking:
    def test_second_charge_on_paid_invoice_is_rejected(
        self, public_client, sent_invoice
    ):
        """The per-invoice re-check (under select_for_update) means a charge on an
        invoice that became paid is rejected with 400 and charges nothing more.

        This is the deterministic, single-threaded analogue of the double-submit
        guard: the second attempt re-reads the (now zero) balance and bails.
        """
        first = _post_charge(public_client, sent_invoice, method=CARD)
        assert first.status_code == 200
        assert Payment.objects.filter(processor="fake").count() == 1

        second = _post_charge(public_client, sent_invoice, method=CARD)
        assert second.status_code == 400
        # No second Payment created.
        assert Payment.objects.filter(processor="fake").count() == 1
