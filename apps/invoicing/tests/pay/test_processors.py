"""Unit tests for the processor factory and the FakeProcessor lifecycle.

These exercise the normalized contract (statuses, ChargeResult, WebhookEvent,
exceptions) without any database or HTTP layer.
"""

import pytest

from apps.invoicing.processors import (
    BANK,
    CARD,
    FAILED,
    PENDING,
    REFUNDED,
    RETURNED,
    SUCCEEDED,
    ChargeError,
    ProcessorConfigError,
    WebhookEvent,
    get_processor,
)
from apps.invoicing.processors.fake import FakeProcessor
from apps.invoicing.processors.lawpay import LawPayProcessor


# ---------------------------------------------------------------------------
# get_processor() factory
# ---------------------------------------------------------------------------
class TestGetProcessor:
    def test_default_is_fake(self):
        """With PAYMENT_PROCESSOR=fake (the test default) the factory returns a
        FakeProcessor."""
        processor = get_processor()
        assert isinstance(processor, FakeProcessor)
        assert processor.name == "fake"

    def test_explicit_fake(self):
        assert isinstance(get_processor("fake"), FakeProcessor)

    def test_lawpay_with_keys_returns_lawpay(self, settings):
        """With a LawPay secret key configured, the factory returns a
        LawPayProcessor (construction touches no network)."""
        settings.LAWPAY_SECRET_KEY = "sk_test"
        processor = get_processor("lawpay")
        assert isinstance(processor, LawPayProcessor)
        assert processor.name == "lawpay"

    def test_lawpay_without_keys_raises_config_error(self, settings):
        """With no LAWPAY_SECRET_KEY the real processor raises
        ProcessorConfigError (the documented misconfig path)."""
        settings.LAWPAY_SECRET_KEY = ""
        with pytest.raises(ProcessorConfigError):
            get_processor("lawpay")

    def test_unknown_name_raises(self):
        with pytest.raises(ProcessorConfigError):
            get_processor("bogus")


# ---------------------------------------------------------------------------
# FakeProcessor.charge
# ---------------------------------------------------------------------------
class TestFakeCharge:
    def _charge(self, token, method):
        return FakeProcessor().charge(
            token=token,
            amount_cents=10000,
            reference="invoice:1",
            method=method,
        )

    def test_card_ok_succeeds_immediately(self):
        result = self._charge("fake-ok", CARD)
        assert result.status == SUCCEEDED
        assert result.accepted is True
        assert result.is_pending is False
        assert result.method == CARD
        assert result.amount_cents == 10000
        assert result.processor == "fake"
        assert result.transaction_id

    def test_bank_ok_is_pending(self):
        result = self._charge("fake-ok", BANK)
        assert result.status == PENDING
        assert result.accepted is True
        assert result.is_pending is True
        assert result.method == BANK

    def test_decline_raises_charge_error(self):
        with pytest.raises(ChargeError) as exc_info:
            self._charge("fake-decline", CARD)
        assert exc_info.value.code == "declined"

    def test_ach_return_token_is_accepted_pending(self):
        """The return only happens later (at settlement); the charge itself is
        accepted as PENDING."""
        result = self._charge("fake-ach-return", BANK)
        assert result.status == PENDING
        assert result.accepted is True

    def test_fetch_transaction_round_trips(self):
        result = self._charge("fake-ok", CARD)
        fetched = FakeProcessor().fetch_transaction(result.transaction_id)
        assert fetched.transaction_id == result.transaction_id
        assert fetched.status == SUCCEEDED
        assert fetched.amount_cents == 10000

    def test_fetch_unknown_transaction_raises(self):
        with pytest.raises(ChargeError):
            FakeProcessor().fetch_transaction("nope")


# ---------------------------------------------------------------------------
# FakeProcessor.refund
# ---------------------------------------------------------------------------
class TestFakeRefund:
    def test_full_refund_marks_refunded(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ok", amount_cents=10000, reference="invoice:1", method=CARD
        )
        refunded = proc.refund(transaction_id=charged.transaction_id)
        assert refunded.status == REFUNDED

    def test_partial_refund_keeps_status(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ok", amount_cents=10000, reference="invoice:1", method=CARD
        )
        refunded = proc.refund(transaction_id=charged.transaction_id, amount_cents=4000)
        assert refunded.status == SUCCEEDED

    def test_refund_unknown_transaction_raises(self):
        with pytest.raises(ChargeError):
            FakeProcessor().refund(transaction_id="nope")


# ---------------------------------------------------------------------------
# Settlement / return simulation (the async ACH step)
# ---------------------------------------------------------------------------
class TestSettlementSimulation:
    def test_pending_ach_settles_to_succeeded(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ok", amount_cents=10000, reference="invoice:1", method=BANK
        )
        assert charged.status == PENDING

        event = proc.simulate_settlement(charged.transaction_id)
        assert isinstance(event, WebhookEvent)
        assert event.status == SUCCEEDED
        assert event.transaction_id == charged.transaction_id
        # The confirmed state is what a re-fetch now reports.
        assert proc.fetch_transaction(charged.transaction_id).status == SUCCEEDED

    def test_ach_return_settles_to_returned(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ach-return",
            amount_cents=10000,
            reference="invoice:1",
            method=BANK,
        )
        event = proc.simulate_settlement(charged.transaction_id)
        assert event.status == RETURNED

    def test_ach_fail_settles_to_failed(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ach-fail",
            amount_cents=10000,
            reference="invoice:1",
            method=BANK,
        )
        event = proc.simulate_settlement(charged.transaction_id)
        assert event.status == FAILED

    def test_simulate_event_forces_status(self):
        proc = FakeProcessor()
        charged = proc.charge(
            token="fake-ok", amount_cents=10000, reference="invoice:1", method=BANK
        )
        event = proc.simulate_event(charged.transaction_id, RETURNED)
        assert event.status == RETURNED
        assert proc.fetch_transaction(charged.transaction_id).status == RETURNED
