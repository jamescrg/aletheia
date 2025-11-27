from decimal import Decimal

import pytest

from apps.activity.time.models import TimeEntry

pytestmark = pytest.mark.django_db


def test_string(entry):
    assert str(entry) == f"{entry.actions}"


def test_content(entry):
    expected_values = {
        "date": "2020-01-07",
        "actions": "Call with client",
        "hours": 0.2,
    }
    for key, val in expected_values.items():
        assert getattr(entry, key) == val


# -----------------------------------------------------
# property tests
# -----------------------------------------------------
def test_fee(entry):
    # entry has hours=0.2, rate=300
    expected_fee = Decimal("0.2") * 300
    assert entry.fee == expected_fee


def test_fee_calculation(user, matter):
    entry = TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Test work",
        hours=Decimal("2.5"),
        rate=400,
        comp=False,
    )
    assert entry.fee == Decimal("2.5") * 400  # 1000


def test_discounted_fee_when_comped(user, matter):
    entry = TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Pro bono work",
        hours=Decimal("1.5"),
        rate=300,
        comp=True,
    )
    # When comped, discounted_fee returns the fee value
    assert entry.discounted_fee == Decimal("1.5") * 300  # 450


def test_discounted_fee_when_not_comped(entry):
    # entry has comp=False by default
    assert entry.comp is False
    assert entry.discounted_fee == 0
