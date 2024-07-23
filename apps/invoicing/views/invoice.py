from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView

from apps.invoicing.forms import InvoiceForm
from apps.invoicing.models import Invoice
from apps.matters.models import Matter


@login_required
def index(request):
    invoices = (
        Invoice.objects.all()
        .select_related("matter", "created_by")
        .order_by("-created_at")
    )

    context = {
        "page": "invoicing",
        "invoices": invoices,
    }

    return render(request, "invoicing/list.html", context)


class NewInvoiceView(FormView):
    template_name = "invoicing/new-invoice.html"
    form_class = InvoiceForm
    success_url = reverse_lazy("invoicing:invoicing")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = self.form_class()

        # TODO: This
        # Queryset matters that have unbilled time or expenses
        # They do not have an invoice and are unentered
        matter_list = Matter.objects.filter(status="Open").order_by("name")
        form.fields["matter"].queryset = matter_list

        context["form"] = form

        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        form.save()

        return super().form_valid(form)
