import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from apps.activity.expenses.models import ExpenseEntry

pytestmark = pytest.mark.django_db


def test_index(client):
    response = client.get("/activity/expenses/")
    assert response.status_code == 200
    response = client.get(reverse("activity:expenses-index"))
    assert response.status_code == 200
    assertTemplateUsed(response, "activity/expenses/main.html")
    assert response.context["app"] == "activity"


def test_list(client):
    response = client.get("/activity/expenses/list/")
    assert response.status_code == 200
    assertTemplateUsed(response, "activity/expenses/list.html")


def test_add_get(client):
    response = client.get("/activity/expenses/add")
    assert response.status_code == 200
    assertTemplateUsed(response, "activity/expenses/form.html")
    assert response.context["add"]


def test_add_post(client, expense_data):
    response = client.post(reverse("activity:expenses-add"), expense_data)
    assert response.status_code == 204
    found = ExpenseEntry.objects.filter(description=expense_data["description"]).first()
    assert found


def test_edit_get(client, expense):
    response = client.get(f"/activity/expenses/{expense.id}/edit")
    assert response.status_code == 200
    assertTemplateUsed(response, "activity/expenses/form.html")


def test_edit_post(client, matter, expense):
    data = {
        "date": "2022-12-01",
        "matter": matter.id,
        "description": "Updated expense description",
        "amount": "200.00",
        "category": "Postage",
        "comp": False,
        "entered": False,
    }
    response = client.post(f"/activity/expenses/{expense.id}/edit", data)
    assert response.status_code == 204
    found = ExpenseEntry.objects.filter(
        description="Updated expense description"
    ).exists()
    assert found


def test_delete(client, expense):
    response = client.get(f"/activity/expenses/{expense.id}/delete")
    assert response.status_code == 204
    found = ExpenseEntry.objects.filter(pk=expense.id).exists()
    assert not found


def test_toggle_entered(client, expense):
    assert expense.entered is False
    client.get(f"/activity/expenses/{expense.id}/toggle-entered")
    expense.refresh_from_db()
    assert expense.entered is True


def test_filter_get(client):
    response = client.get("/activity/expenses/filter/")
    assert response.status_code == 200
    assertTemplateUsed(response, "activity/expenses/filter.html")


def test_filter_post(client):
    response = client.post("/activity/expenses/filter/")
    assert response.status_code == 204


def test_filter_quick_unbilled(client):
    response = client.get("/activity/expenses/filter/quick/unbilled")
    assert response.status_code == 204


def test_filter_quick_today(client):
    response = client.get("/activity/expenses/filter/quick/today")
    assert response.status_code == 204


def test_export_clio(client):
    response = client.get("/activity/expenses/export/clio")
    assert response.status_code == 200


def test_export_standard(client):
    response = client.get("/activity/expenses/export/standard")
    assert response.status_code == 200
