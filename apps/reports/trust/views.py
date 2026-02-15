from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Case, DecimalField, Sum, Value, When
from django.shortcuts import render

from apps.trust.models import Transaction


def _get_trust_data(sort_by="client_name", sort_direction="asc"):
    """Build trust balance data grouped by client."""
    client_data = (
        Transaction.objects.filter(contact__isnull=False)
        .values("contact__id", "contact__name")
        .annotate(
            deposits=Sum(
                Case(
                    When(type="Deposit", then="amount"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            ),
            disbursements=Sum(
                Case(
                    When(type="Withdrawal", then="amount"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            ),
        )
    )

    results = []
    total_deposits = 0
    total_disbursements = 0
    total_balance = 0

    for row in client_data:
        deposits = row["deposits"] or 0
        disbursements = row["disbursements"] or 0
        balance = deposits - disbursements

        if balance == 0:
            continue

        results.append(
            {
                "client_id": row["contact__id"],
                "client_name": row["contact__name"] or "Unknown",
                "deposits": deposits,
                "disbursements": disbursements,
                "balance": balance,
            }
        )
        total_deposits += deposits
        total_disbursements += disbursements
        total_balance += balance

    # Sort
    reverse_sort = sort_direction == "desc"
    if sort_by == "client_name":
        results.sort(key=lambda x: x["client_name"].lower(), reverse=reverse_sort)
    elif sort_by == "balance":
        results.sort(key=lambda x: x["balance"], reverse=reverse_sort)
    elif sort_by == "deposits":
        results.sort(key=lambda x: x["deposits"], reverse=reverse_sort)
    elif sort_by == "disbursements":
        results.sort(key=lambda x: x["disbursements"], reverse=reverse_sort)

    totals = {
        "deposits": total_deposits,
        "disbursements": total_disbursements,
        "balance": total_balance,
    }

    return results, totals


@login_required
@staff_member_required
def trust_index(request):
    sort_by = request.GET.get("sort", "client_name")
    sort_direction = request.GET.get("direction", "asc")
    trust_data, totals = _get_trust_data(sort_by, sort_direction)

    context = {
        "app": "reports",
        "subapp": "trust",
        "trust_data": trust_data,
        "totals": totals,
        "current_sort": sort_by,
        "current_direction": sort_direction,
    }
    return render(request, "reports/trust/main.html", context)


@login_required
@staff_member_required
def trust_list(request):
    sort_by = request.GET.get("sort", "client_name")
    sort_direction = request.GET.get("direction", "asc")
    trust_data, totals = _get_trust_data(sort_by, sort_direction)

    context = {
        "app": "reports",
        "subapp": "trust",
        "trust_data": trust_data,
        "totals": totals,
        "current_sort": sort_by,
        "current_direction": sort_direction,
    }
    return render(request, "reports/trust/list.html", context)
