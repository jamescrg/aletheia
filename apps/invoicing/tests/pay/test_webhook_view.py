"""Tests for the ``processor_webhook`` HTTP entrypoint.

The view enqueues reconciliation on Django-Q and falls back to running it inline
if the queue is unavailable. We mock ``django_q.tasks.async_task`` so tests don't
touch a broker: a no-op to assert the 200/enqueue contract, and a raising mock to
exercise the inline-reconcile fallback end-to-end.
"""

import json
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.invoicing.applications.models import PaymentApplication
from apps.invoicing.pay.recording import record_payment
from apps.invoicing.payments.models import Payment
from apps.invoicing.processors import BANK, get_processor

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_client():
    return Client()


def _webhook_url():
    return reverse("pay:webhook", kwargs={"processor": "fake"})


def _charge_and_record(invoice, *, token, method):
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


def test_webhook_enqueues_and_returns_200(public_client):
    body = json.dumps({"transaction_id": "fake_x", "status": "returned"})
    with mock.patch("django_q.tasks.async_task") as async_task:
        response = public_client.post(
            _webhook_url(), data=body, content_type="application/json"
        )
    assert response.status_code == 200
    async_task.assert_called_once()
    # Reconciler name + processor + raw body are handed to the task.
    args = async_task.call_args.args
    assert args[0] == "apps.invoicing.pay.reconcile.reconcile_webhook"
    assert args[1] == "fake"


def test_webhook_inline_fallback_reconciles(
    public_client, sent_invoice, settings, mailoutbox
):
    """If the queue is down, the view reconciles inline — a returned ACH charge
    is reversed end-to-end through the HTTP entrypoint."""
    settings.ADMINS = [("Admin", "admin@example.test")]
    payment, result = _charge_and_record(
        sent_invoice, token="fake-ach-return", method=BANK
    )
    sent_invoice.refresh_from_db()
    assert sent_invoice.status == "PAID"

    body = json.dumps({"transaction_id": result.transaction_id, "status": "returned"})
    with mock.patch(
        "django_q.tasks.async_task", side_effect=RuntimeError("queue down")
    ):
        response = public_client.post(
            _webhook_url(), data=body, content_type="application/json"
        )

    assert response.status_code == 200
    assert not Payment.objects.filter(pk=payment.pk).exists()
    assert not PaymentApplication.objects.filter(payment=payment).exists()
    sent_invoice.refresh_from_db()
    assert sent_invoice.status == "SENT"
    assert len(mailoutbox) == 1
