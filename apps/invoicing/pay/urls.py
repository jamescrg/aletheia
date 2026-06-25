from django.urls import path

from apps.invoicing.pay.views import pay_charge, pay_page

app_name = "pay"

urlpatterns = [
    # Public, tokenized — no login. The signed token carries the invoice uuid.
    path("pay/<str:token>/", pay_page, name="invoice"),
    path("pay/<str:token>/charge/", pay_charge, name="charge"),
]
