"""Revenue report aggregation — revenue attributed to users.

`build_revenue_context` resolves the same rolling WINDOW_MONTHS window as the
Activity report and, for every payment in the window, attributes the cash to the
users whose billable hours it covered. Each payment is followed through its
`PaymentApplication`s to the paid invoices; the applied amount is split across the
invoice's net (non-comp) line items pro-rata by value. The time-fee portion is
credited to each entry's user; the expense and flat-fee portions go to dedicated
"Expenses" / "Flat fees" buckets (not anyone's revenue); unapplied cash and
user-less time go to "Unapplied" / "Unassigned". Every month's stack therefore
reconciles exactly to the cash collected that month (Σ Payment.amount).

Cash basis: a month column counts payments by their `Payment.date`. The window's
end month is held in the session ("revenue_end") and stepped by `revenue_period`.
"""

from collections import defaultdict
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import DecimalField, F, Sum

from apps.accounts.models import CustomUser
from apps.activity.expenses.models import ExpenseEntry
from apps.activity.flat_fees.models import FlatFeeEntry
from apps.activity.time.models import TimeEntry
from apps.invoicing.applications.models import PaymentApplication
from apps.invoicing.payments.models import Payment
from apps.reports.activity.aggregation import _window_months, resolve_end

CENT = Decimal("0.01")

# Non-user catch-all buckets, in trailing display order after the user rows.
EXPENSES = "Expenses"
FLAT_FEES = "Flat fees"
UNASSIGNED = "Unassigned"
UNAPPLIED = "Unapplied"
TRAILING_BUCKETS = (EXPENSES, FLAT_FEES, UNASSIGNED, UNAPPLIED)

# On the chart, expenses + flat fees + unapplied collapse into one grey series.
GROUP_LABEL = "Other (expenses, flat fees, unapplied)"


def build_revenue_context(request):
    """Full template context for the revenue report, including `chart_payload`."""
    end, current_first = resolve_end(request.session.get("revenue_end"))
    months = _window_months(end)
    n = len(months)
    window_start = months[0]["date"]
    window_end = months[-1]["date"] + relativedelta(months=1)
    month_index = {(m["year"], m["month"]): i for i, m in enumerate(months)}

    # 1) Payment totals (also catches payments with no applications at all).
    payments = list(
        Payment.objects.filter(date__gte=window_start, date__lt=window_end).values(
            "id", "date", "amount"
        )
    )

    # 2) Applications in the window: the (payment, invoice, applied) rows.
    app_rows = list(
        PaymentApplication.objects.filter(
            payment__date__gte=window_start, payment__date__lt=window_end
        ).values("payment_id", "invoice_id", "amount_applied")
    )
    invoice_ids = {r["invoice_id"] for r in app_rows}
    apps_by_payment = defaultdict(list)
    for r in app_rows:
        apps_by_payment[r["payment_id"]].append(r)

    # 3) Per-(invoice, user) net time fees (non-comp).
    time_by_invoice = defaultdict(dict)
    for r in (
        TimeEntry.objects.filter(invoice_id__in=invoice_ids, comp=False)
        .values("invoice_id", "user_id")
        .annotate(
            net=Sum(
                F("hours") * F("rate"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    ):
        time_by_invoice[r["invoice_id"]][r["user_id"]] = Decimal(r["net"] or 0)

    # 4) Per-invoice net expenses and flat fees (non-comp), kept separate.
    expense_by_invoice = defaultdict(lambda: Decimal(0))
    for r in (
        ExpenseEntry.objects.filter(invoice_id__in=invoice_ids, comp=False)
        .values("invoice_id")
        .annotate(net=Sum("amount"))
    ):
        expense_by_invoice[r["invoice_id"]] = Decimal(r["net"] or 0)

    flatfee_by_invoice = defaultdict(lambda: Decimal(0))
    for r in (
        FlatFeeEntry.objects.filter(invoice_id__in=invoice_ids, comp=False)
        .values("invoice_id")
        .annotate(net=Sum("amount"))
    ):
        flatfee_by_invoice[r["invoice_id"]] = Decimal(r["net"] or 0)

    # Ordered (bucket_key, value) parts for an invoice, computed once per invoice.
    # bucket_key is ("u", user_id) for a user or ("b", name) for a catch-all.
    parts_cache = {}

    def invoice_parts(invoice_id):
        cached = parts_cache.get(invoice_id)
        if cached is not None:
            return cached
        parts = []
        for uid, net in time_by_invoice.get(invoice_id, {}).items():
            if net > 0:
                key = ("u", uid) if uid is not None else ("b", UNASSIGNED)
                parts.append((key, net))
        if expense_by_invoice[invoice_id] > 0:
            parts.append((("b", EXPENSES), expense_by_invoice[invoice_id]))
        if flatfee_by_invoice[invoice_id] > 0:
            parts.append((("b", FLAT_FEES), flatfee_by_invoice[invoice_id]))
        parts_cache[invoice_id] = parts
        return parts

    # buckets[key] -> per-month list of Decimals.
    buckets = defaultdict(lambda: [Decimal(0)] * n)

    for p in payments:
        idx = month_index[(p["date"].year, p["date"].month)]
        amount = Decimal(p["amount"])
        p_apps = apps_by_payment.get(p["id"], [])
        applied_sum = sum((Decimal(a["amount_applied"]) for a in p_apps), Decimal(0))

        unapplied = amount - applied_sum
        if unapplied != 0:
            buckets[("b", UNAPPLIED)][idx] += unapplied

        for a in p_apps:
            applied = Decimal(a["amount_applied"])
            parts = invoice_parts(a["invoice_id"])
            net_total = sum((v for _, v in parts), Decimal(0))
            if net_total <= 0:
                # Comp-only or empty invoice: nothing billable to attribute to.
                buckets[("b", UNASSIGNED)][idx] += applied
                continue
            # Pro-rata across parts; the last part absorbs the rounding remainder
            # so the shares sum to `applied` exactly.
            remaining = applied
            last = len(parts) - 1
            for i, (key, value) in enumerate(parts):
                if i == last:
                    share = remaining
                else:
                    share = (applied * value / net_total).quantize(CENT)
                    remaining -= share
                buckets[key][idx] += share

    # User display labels for the user buckets.
    user_ids = [key[1] for key in buckets if key[0] == "u"]
    users = {
        u["id"]: u
        for u in CustomUser.objects.filter(id__in=user_ids).values(
            "id", "first_name", "last_name", "username"
        )
    }

    def label_for(key):
        if key[0] == "b":
            return key[1]
        u = users.get(key[1])
        if not u:
            return "Unknown"
        return f"{u['first_name']} {u['last_name']}".strip() or u["username"]

    user_keys = sorted(
        (key for key in buckets if key[0] == "u"),
        key=lambda k: label_for(k).lower(),
    )

    # Table: every bucket broken out individually (users, then catch-alls).
    table_keys = user_keys + [("b", name) for name in TRAILING_BUCKETS]
    revenue_rows = []
    month_totals = [Decimal(0)] * n
    grand_total = Decimal(0)
    for key in table_keys:
        data = buckets.get(key)
        if data is None:
            continue
        row_total = sum(data, Decimal(0))
        if row_total == 0:
            continue
        revenue_rows.append(
            {
                "label": label_for(key),
                "cells": [{"amount": v} for v in data],
                "total": row_total,
            }
        )
        for i in range(n):
            month_totals[i] += data[i]
        grand_total += row_total

    # Each cell's share of that month's revenue; each row's share of the total.
    for row in revenue_rows:
        row["pct"] = (row["total"] / grand_total * 100) if grand_total else Decimal(0)
        for i, cell in enumerate(row["cells"]):
            month_total = month_totals[i]
            cell["pct"] = (
                (cell["amount"] / month_total * 100) if month_total else Decimal(0)
            )

    if settings.DEBUG:
        # Reconciliation: the attributed buckets must equal the cash collected.
        cash = sum((Decimal(p["amount"]) for p in payments), Decimal(0))
        assert grand_total == cash, f"revenue mismatch: {grand_total} != {cash}"

    # Chart: one series per user, "Unassigned" on its own, and expenses + flat
    # fees + unapplied folded into a single neutral (grey) "Other" series.
    def series_from(key, label):
        data = buckets.get(key)
        if not data or sum(data, Decimal(0)) == 0:
            return None
        return {"label": label, "fees": [float(round(v, 2)) for v in data]}

    series = [s for s in (series_from(k, label_for(k)) for k in user_keys) if s]
    unassigned = series_from(("b", UNASSIGNED), UNASSIGNED)
    if unassigned:
        series.append(unassigned)

    grouped = [Decimal(0)] * n
    for name in (EXPENSES, FLAT_FEES, UNAPPLIED):
        data = buckets.get(("b", name))
        if data:
            for i in range(n):
                grouped[i] += data[i]
    if sum(grouped, Decimal(0)) != 0:
        series.append(
            {
                "label": GROUP_LABEL,
                "fees": [float(round(v, 2)) for v in grouped],
                "neutral": True,
            }
        )

    chart_payload = {
        "months": [m["name"] for m in months],
        "series": {"user": series},
    }

    return {
        "app": "reports",
        "subapp": "revenue",
        "months": months,
        "revenue_rows": revenue_rows,
        "month_totals": [{"amount": v} for v in month_totals],
        "grand_total": grand_total,
        "period_label": end.strftime("%b %Y"),
        "can_go_next": end < current_first,
        "chart_payload": chart_payload,
    }
