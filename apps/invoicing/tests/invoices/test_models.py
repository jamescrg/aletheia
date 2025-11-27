from decimal import Decimal

import pytest

from apps.activity.expenses.models import ExpenseEntry
from apps.activity.time.models import TimeEntry
from apps.invoicing.invoices.models import Invoice

pytestmark = pytest.mark.django_db


# -----------------------------------------------------
# __str__ tests
# -----------------------------------------------------
def test_string(invoice):
    assert str(invoice) == f"Invoice #{invoice.id}"


# -----------------------------------------------------
# value property tests
# -----------------------------------------------------
def test_value_empty_invoice(invoice_empty):
    value = invoice_empty.value
    assert value["gross_fees"] == 0
    assert value["comp_fees"] == 0
    assert value["net_fees"] == 0
    assert value["gross_expenses"] == 0
    assert value["comp_expenses"] == 0
    assert value["net_expenses"] == 0
    assert value["pre_discount_total"] == 0
    assert value["final_total"] == 0


def test_value_time_only(user, matter):
    # Create a fresh invoice without any pre-existing entries
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Manually create and link a time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Billable work",
        hours=Decimal("2.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    expected_fees = Decimal("2.0") * 300  # hours * rate = 600
    assert value["gross_fees"] == expected_fees
    assert value["net_fees"] == expected_fees
    assert value["gross_expenses"] == 0
    assert value["net_expenses"] == 0
    assert value["final_total"] == expected_fees


def test_value_expenses_only(user, matter):
    # Create a fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Create and link an expense entry
    ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Filing Fee",
        description="Court filing",
        amount=Decimal("150.00"),
        comp=False,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    assert value["gross_fees"] == 0
    assert value["net_fees"] == 0
    assert value["gross_expenses"] == Decimal("150.00")
    assert value["net_expenses"] == Decimal("150.00")
    assert value["final_total"] == Decimal("150.00")


def test_value_mixed(user, matter):
    # Create a fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Create time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Billable work",
        hours=Decimal("2.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    # Create expense entry
    ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Filing Fee",
        description="Court filing",
        amount=Decimal("150.00"),
        comp=False,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    expected_fees = Decimal("2.0") * 300  # 600
    expected_expenses = Decimal("150.00")
    assert value["gross_fees"] == expected_fees
    assert value["net_fees"] == expected_fees
    assert value["gross_expenses"] == expected_expenses
    assert value["net_expenses"] == expected_expenses
    assert value["final_total"] == expected_fees + expected_expenses


def test_value_with_comp_time(user, matter):
    # Create a fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Create billable time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Billable work",
        hours=Decimal("2.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    # Create comped time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Pro bono work",
        hours=Decimal("1.0"),
        rate=300,
        comp=True,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    billable_fees = Decimal("2.0") * 300  # 600
    comped_fees = Decimal("1.0") * 300  # 300
    assert value["gross_fees"] == billable_fees + comped_fees
    assert value["comp_fees"] == comped_fees
    assert value["net_fees"] == billable_fees


def test_value_with_comp_expense(user, matter):
    # Create a fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Create billable expense
    ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Filing Fee",
        description="Court filing",
        amount=Decimal("150.00"),
        comp=False,
        entered=False,
        invoice=invoice,
    )
    # Create comped expense
    ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Postage",
        description="Certified mail",
        amount=Decimal("25.00"),
        comp=True,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    billable_expense = Decimal("150.00")
    comped_expense = Decimal("25.00")
    assert value["gross_expenses"] == billable_expense + comped_expense
    assert value["comp_expenses"] == comped_expense
    assert value["net_expenses"] == billable_expense


def test_value_with_discount(user, matter):
    # Create invoice with discount
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
        discount=Decimal("50.00"),
    )
    # Add time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Work",
        hours=Decimal("1.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    value = invoice.value
    expected_fees = Decimal("1.0") * 300  # 300
    discount = Decimal("50.00")
    assert value["pre_discount_total"] == expected_fees
    assert value["final_total"] == expected_fees - discount


# -----------------------------------------------------
# amount_remaining property tests
# -----------------------------------------------------
def test_amount_remaining_no_payments(user, matter):
    # Create fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    # Add time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Billable work",
        hours=Decimal("2.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    expected_total = Decimal("2.0") * 300  # 600
    assert invoice.amount_remaining == expected_total


def test_amount_remaining_legacy_paid(user, matter):
    # Create fresh invoice
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
        status="PAID",
    )
    # Add time entry
    TimeEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        actions="Billable work",
        hours=Decimal("2.0"),
        rate=300,
        comp=False,
        entered=False,
        invoice=invoice,
    )
    # Legacy behavior: PAID status with no allocations returns 0
    assert invoice.amount_remaining == 0
