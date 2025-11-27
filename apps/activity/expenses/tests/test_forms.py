from decimal import Decimal

import pytest

from apps.activity.expenses.forms import ExpenseEntryForm

pytestmark = pytest.mark.django_db


def test_form_valid(expense_data):
    form = ExpenseEntryForm(expense_data)
    assert form.is_valid()


def test_form_requires_description(expense_data):
    data = expense_data.copy()
    data["description"] = ""
    form = ExpenseEntryForm(data)
    # description is required on the form
    assert not form.is_valid()
    assert "description" in form.errors


def test_amount_decimal(expense_data):
    data = expense_data.copy()
    data["amount"] = Decimal("1234.56")
    form = ExpenseEntryForm(data)
    assert form.is_valid()
    assert form.cleaned_data["amount"] == Decimal("1234.56")
