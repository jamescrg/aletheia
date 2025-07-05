import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from apps.invoicing.invoices.forms import EditInvoiceForm, InvoiceForm
from apps.invoicing.invoices.models import Invoice

pytestmark = pytest.mark.django_db


def test_invoices_list(client, invoice):
    response = client.get(reverse("invoicing:invoices-list"))
    assert response.status_code == 200
    assertTemplateUsed(response, "invoicing/invoices/list.html")
    assert response.context["app"] == "invoicing"
    assert response.context["subapp"] == "invoices"


def test_invoices_detail(client, invoice):
    response = client.get(
        reverse("invoicing:invoices-detail", kwargs={"pk": invoice.pk})
    )
    assert response.status_code == 200
    assertTemplateUsed(response, "invoicing/invoices/time/index.html")
    assert response.context["app"] == "invoicing"

    # Test the invoice calculation
    assert response.context["invoice"].value["final_total"] == 60


def test_invoices_add_get(client):
    response = client.get(reverse("invoicing:invoices-add"))
    assert response.status_code == 200
    assertTemplateUsed(response, "invoicing/invoices/form.html")

    assert isinstance(response.context["form"], InvoiceForm)


def test_invoices_add_post(client, matter, user, invoice_data):
    invoice_data["matter"] = matter.id
    invoice_data["pdf_file"] = None

    cleaned_data = {k: v for k, v in invoice_data.items() if v is not None}

    response = client.post(reverse("invoicing:invoices-add"), cleaned_data)

    assert response.status_code == 204
    assert Invoice.objects.filter(matter=matter).exists()


def test_invoices_edit_get(client, invoice):
    response = client.get(reverse("invoicing:invoices-edit", kwargs={"pk": invoice.pk}))
    assert response.status_code == 200
    assertTemplateUsed(response, "invoicing/invoices/edit.html")
    assert isinstance(response.context["form"], EditInvoiceForm)
    assert "invoice" in response.context


def test_invoices_edit_status(client, invoice):
    response = client.post(
        reverse(
            "invoicing:invoices-edit-status",
            kwargs={"pk": invoice.pk, "status": "PAID", "view": "list"},
        )
    )
    assert response.status_code == 204

    invoice.refresh_from_db()
    assert invoice.status == "PAID"


def test_invoices_delete(client, invoice):
    response = client.post(
        reverse("invoicing:invoices-delete", kwargs={"pk": invoice.pk})
    )
    assert response.status_code == 302
    assert not Invoice.objects.filter(pk=invoice.pk).exists()


def test_invoices_pdf(client, invoice):
    response = client.get(reverse("invoicing:invoices-pdf", kwargs={"pk": invoice.pk}))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "Content-Disposition" in response


def test_invoices_filter_get(client):
    response = client.get(reverse("invoicing:invoices-filter"))
    assert response.status_code == 200
    assertTemplateUsed(response, "invoicing/invoices/filter.html")


def test_invoices_filter_post(client):
    filter_data = {"status": "PAID"}
    response = client.post(reverse("invoicing:invoices-filter"), filter_data)
    assert response.status_code == 204


def test_invoices_filter_status(client):
    response = client.post(
        reverse("invoicing:invoices-filter-status", kwargs={"status": "PAID"})
    )
    assert response.status_code == 204
