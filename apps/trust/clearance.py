"""Per-client trust clearance for the Account Summary table.

Clearance is the confirmed trust balance that is *free of current obligations*:

    clearance(client) = confirmed trust balance
                      − currently owed across the client's non-deferred invoices
                      − unbilled net fees/expenses on the client's non-deferred-fee matters

This is the client-level aggregate of the per-matter figure in
``apps.matters.ledger.get_ledger_data.compute_trust_clearance`` — a client's trust
is a single pooled balance that all their matters draw on, so it nets against the
sum of all their obligations. It intentionally differs from the matter ledger
tab's per-matter clearance (different scope).

``attach_client_clearance`` sets ``contact["clearance"]`` (a ``Decimal``) on each
summary row dict using bulk queries (a handful total, not one per client), so the
whole summary can be computed and sorted before pagination.
"""

from collections import defaultdict
from decimal import Decimal

from django.db.models import DecimalField, F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce


def _coalesced_sum(queryset, group_field, expr):
    """A correlated per-parent ``Sum`` subquery, 0 when there are no rows.

    ``queryset`` is already filtered to ``<group_field>=OuterRef("pk")``; grouping
    by that field yields a single row (the sum for the outer object).
    """
    dec = DecimalField(max_digits=14, decimal_places=2)
    return Coalesce(
        Subquery(
            queryset.values(group_field)
            .annotate(total=Sum(expr, output_field=dec))
            .values("total"),
            output_field=dec,
        ),
        0,
        output_field=dec,
    )


def attach_client_clearance(contacts):
    """Set ``contact["clearance"]`` (Decimal) on each Account Summary row dict.

    Each dict already carries ``id`` and ``confirmed_client_balance`` from the
    trust balance passes. Returns the same list.
    """
    from apps.activity.expenses.models import ExpenseEntry
    from apps.activity.flat_fees.models import FlatFeeEntry
    from apps.activity.time.models import TimeEntry
    from apps.invoicing.applications.models import (
        CreditApplication,
        PaymentApplication,
    )
    from apps.invoicing.invoices.models import Invoice
    from apps.matters.models import Matter

    client_ids = [c["id"] for c in contacts]
    if not client_ids:
        return contacts

    fee = F("hours") * F("rate")  # time-entry fee = hours × rate
    zero = Decimal("0")

    # --- currently owed per client -----------------------------------------
    # Reproduce Invoice.amount_remaining over the client's DISPLAYED, non-deferred
    # invoices (mirrors get_ledger_data's currently_owed). amount_remaining has
    # Python-only branches (VOID/UNCOLLECTIBLE and legacy PAID-without-allocations
    # → 0), so we bulk-annotate the components and finish the arithmetic in Python.
    invoices = (
        Invoice.objects.filter(matter__client_id__in=client_ids)
        .exclude(status__in=["DRAFT", "APPROVED"])
        .annotate(
            net_fees=_coalesced_sum(
                TimeEntry.objects.filter(invoice=OuterRef("pk")).exclude(comp=True),
                "invoice",
                fee,
            ),
            net_exp=_coalesced_sum(
                ExpenseEntry.objects.filter(invoice=OuterRef("pk")).exclude(comp=True),
                "invoice",
                F("amount"),
            ),
            net_flat=_coalesced_sum(
                FlatFeeEntry.objects.filter(invoice=OuterRef("pk")).exclude(comp=True),
                "invoice",
                F("amount"),
            ),
            pay=_coalesced_sum(
                PaymentApplication.objects.filter(invoice=OuterRef("pk")),
                "invoice",
                F("amount_applied"),
            ),
            cred=_coalesced_sum(
                CreditApplication.objects.filter(invoice=OuterRef("pk")),
                "invoice",
                F("amount_applied"),
            ),
        )
        .values(
            "matter__client_id",
            "status",
            "discount",
            "net_fees",
            "net_exp",
            "net_flat",
            "pay",
            "cred",
        )
    )
    owed = defaultdict(Decimal)
    for inv in invoices:
        status = inv["status"]
        if status == "DEFERRED":
            continue  # deferred recovery claim, not currently owed
        if status in ("VOID", "UNCOLLECTIBLE"):
            remaining = zero
        else:
            final_total = (
                inv["net_fees"]
                + inv["net_exp"]
                + inv["net_flat"]
                - (inv["discount"] or zero)
            )
            if status == "PAID" and inv["pay"] == 0 and inv["cred"] == 0:
                remaining = zero  # legacy PAID without allocations
            else:
                remaining = final_total - inv["pay"] - inv["cred"]
        owed[inv["matter__client_id"]] += remaining

    # --- unbilled net fees/expenses per client -----------------------------
    # Sum of Matter.value["unbilled"]["net_fees_and_expenses"] over the client's
    # non-deferred-fee matters (deferred-fee matters accrue but aren't collectible).
    matters = (
        Matter.objects.filter(client_id__in=client_ids, deferred_fees=False)
        .annotate(
            net_fees=_coalesced_sum(
                TimeEntry.objects.filter(
                    matter=OuterRef("pk"), entered=False, invoice__isnull=True
                ).exclude(comp=True),
                "matter",
                fee,
            ),
            net_exp=_coalesced_sum(
                ExpenseEntry.objects.filter(
                    matter=OuterRef("pk"), entered=False, invoice__isnull=True
                ).exclude(comp=True),
                "matter",
                F("amount"),
            ),
            net_flat=_coalesced_sum(
                FlatFeeEntry.objects.filter(
                    matter=OuterRef("pk"), entered=False, invoice__isnull=True
                ).exclude(comp=True),
                "matter",
                F("amount"),
            ),
        )
        .values("client_id", "net_fees", "net_exp", "net_flat")
    )
    unbilled = defaultdict(Decimal)
    for m in matters:
        unbilled[m["client_id"]] += m["net_fees"] + m["net_exp"] + m["net_flat"]

    for c in contacts:
        confirmed = c.get("confirmed_client_balance") or zero
        c["clearance"] = (
            confirmed - owed.get(c["id"], zero) - unbilled.get(c["id"], zero)
        )
    return contacts
