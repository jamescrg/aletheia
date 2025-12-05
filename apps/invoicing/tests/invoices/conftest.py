from decimal import Decimal

import pytest
from django.test import Client

from apps.accounts.models import CustomUser
from apps.activity.expenses.models import ExpenseEntry
from apps.activity.time.models import TimeEntry
from apps.invoicing.invoices.models import Invoice
from apps.matters.models import Matter, PracticeArea


@pytest.fixture
def user():
    user = CustomUser.objects.create(
        username="Ollie", email="ollie@gmail.com", user_rate=100
    )
    user.set_password("clawboy")
    user.save()

    return user


@pytest.fixture
def client(user):
    client = Client()
    client.login(username="Ollie", password="clawboy")
    client.get("/dash/")  # Set daily dash session to avoid redirect
    return client


@pytest.fixture
def practice_area():
    practice_area = PracticeArea.objects.create(name="General", is_active=True)
    return practice_area


@pytest.fixture
def matter(practice_area):
    matter = Matter.objects.create(
        name="Sample Test Matter",
        work_status="Awaiting response from OC",
        status="Open",
        practice_area=practice_area,
    )

    return matter


@pytest.fixture
def entry(user, matter):
    entry = TimeEntry.objects.create(
        user_id=user.id,
        matter=matter,
        date="2020-01-07",
        actions="Call with client",
        hours=0.2,
        rate=300,
        comp=False,
        entered=False,
    )
    entry.save()
    return entry


@pytest.fixture
def invoice(user, matter, entry):
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2024-12-31",
        date_issued="2024-12-01",
    )

    return invoice


@pytest.fixture
def invoice_data(invoice):
    exclude_keys = {"_state", "id", "matter_id", "created_by_id"}

    invoice_data = {
        key: value for key, value in invoice.__dict__.items() if key not in exclude_keys
    }

    invoice_data["matter"] = invoice.matter_id

    return invoice_data


@pytest.fixture
def invoice_empty(user, matter):
    """Invoice with no time or expense entries."""
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2020-01-01",
        date_issued="2020-01-01",
    )
    return invoice


@pytest.fixture
def time_entry_for_invoice(user, matter, invoice):
    """Time entry linked to the invoice fixture."""
    entry = TimeEntry.objects.create(
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
    return entry


@pytest.fixture
def time_entry_comped(user, matter, invoice):
    """Comped time entry linked to invoice."""
    entry = TimeEntry.objects.create(
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
    return entry


@pytest.fixture
def expense_entry_for_invoice(user, matter, invoice):
    """Expense entry linked to the invoice fixture."""
    expense = ExpenseEntry.objects.create(
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
    return expense


@pytest.fixture
def expense_entry_comped(user, matter, invoice):
    """Comped expense entry linked to invoice."""
    expense = ExpenseEntry.objects.create(
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
    return expense


@pytest.fixture
def invoice_with_discount(user, matter, entry):
    """Invoice with a discount applied."""
    invoice = Invoice.objects.create(
        created_by=user,
        matter=matter,
        date_limit="2024-12-31",
        date_issued="2024-12-01",
        discount=Decimal("50.00"),
    )
    return invoice
