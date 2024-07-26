from django.urls import path

from apps.invoicing.views.invoice import (
    DeleteInvoiceView,
    InvoiceActivityView,
    InvoiceDetailView,
    InvoiceExpensesView,
    NewInvoiceView,
    index,
)

app_name = "invoicing"

urlpatterns = [
    path("invoicing/", index, name="invoicing"),
    path(
        "invoicing/invoice-detail/<int:pk>/preview/",
        InvoiceDetailView.as_view(),
        name="invoice-detail",
    ),
    path(
        "invoicing/invoice-detail/<int:pk>/entries/",
        InvoiceActivityView.as_view(),
        name="invoice-activity",
    ),
    path(
        "invoicing/invoice-detail/<int:pk>/expenses/",
        InvoiceExpensesView.as_view(),
        name="invoice-expenses",
    ),
    path("invoicing/new-invoice/", NewInvoiceView.as_view(), name="new-invoice"),
    path(
        "invoicing/delete-invoice/<int:pk>/",
        DeleteInvoiceView.as_view(),
        name="delete-invoice",
    ),
]
