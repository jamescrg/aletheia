from decimal import Decimal

import pytest
from django.test import Client

from apps.accounts.models import CustomUser
from apps.activity.expenses.models import ExpenseEntry
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
    matter.save()
    return matter


@pytest.fixture
def expense(user, matter):
    expense = ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Filing Fee",
        description="Court filing fee",
        amount=Decimal("150.00"),
        comp=False,
        entered=False,
    )
    expense.save()
    return expense


@pytest.fixture
def expense_comped(user, matter):
    expense = ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category="Postage",
        description="Certified mail",
        amount=Decimal("25.00"),
        comp=True,
        entered=False,
    )
    expense.save()
    return expense


@pytest.fixture
def expense_data(expense):
    exclude_keys = {"_state", "id", "matter_id", "user_id", "invoice_id"}
    expense_data = {
        key: value for key, value in expense.__dict__.items() if key not in exclude_keys
    }
    expense_data["matter"] = expense.matter_id
    expense_data = {k: v if v is not None else "" for k, v in expense_data.items()}
    return expense_data
