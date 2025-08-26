import os
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.matters.ledger.generate_ledger import generate_ledger
from apps.matters.ledger.get_ledger_data import get_ledger_data
from apps.matters.models import Matter
from apps.trust.trust import get_confirmed_client_balance


@login_required
def ledger_index(request, id):
    matter = get_object_or_404(Matter, pk=id)
    ledger_data = get_ledger_data(matter)

    # Get client trust balance
    client_trust_balance = 0
    if matter.client:
        client_trust_balance = get_confirmed_client_balance(matter.client.id)

    total_cost = (
        matter.value["invoices"]["payment_sum"]
        + ledger_data["balance_due"]
        + matter.value["unbilled"]["net_fees_and_expenses"]
    )

    context = {
        "app": "matters",
        "subapp": "ledger",
        "matter": matter,
        "client_trust_balance": client_trust_balance,
        "total_cost": total_cost,
    } | ledger_data

    return render(request, "matters/ledger/main.html", context)


@login_required
def ledger_list(request, id):
    matter = get_object_or_404(Matter, pk=id)
    ledger_data = get_ledger_data(matter)

    # Get client trust balance
    client_trust_balance = 0
    if matter.client:
        client_trust_balance = get_confirmed_client_balance(matter.client.id)

    context = {
        "app": "matters",
        "subapp": "ledger",
        "matter": matter,
        "client_trust_balance": client_trust_balance,
    } | ledger_data

    return render(request, "matters/ledger/list.html", context)


@login_required
def ledger_pdf(request, pk):
    matter = get_object_or_404(Matter, pk=pk)
    file = generate_ledger(matter.id, request)

    current_date = datetime.now().strftime("%Y-%m-%d")

    with open(file.name, "rb") as pdf:
        response = HttpResponse(pdf.read(), content_type="application/pdf")
        filename = f'filename="Ledger - {matter.name} - {current_date}.pdf"'
        response["Content-Disposition"] = f"attachment; {filename}"

    os.unlink(file.name)

    return response
