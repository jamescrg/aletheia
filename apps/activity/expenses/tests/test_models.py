from decimal import Decimal

import pytest

pytestmark = pytest.mark.django_db


def test_string(expense):
    assert str(expense) == f"{expense.description}"


def test_slug_with_category(expense):
    assert expense.slug == f"{expense.category} - {expense.description}"


def test_slug_without_category(user, matter):
    from apps.activity.expenses.models import ExpenseEntry

    expense = ExpenseEntry.objects.create(
        user=user,
        matter=matter,
        date="2020-01-07",
        category=None,
        description="Miscellaneous expense",
        amount=Decimal("50.00"),
    )
    assert expense.slug == expense.description


def test_discounted_amount_comped(expense_comped):
    assert expense_comped.discounted_amount == expense_comped.amount


def test_discounted_amount_not_comped(expense):
    assert expense.discounted_amount == 0
