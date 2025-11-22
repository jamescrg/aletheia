from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from apps.activity.expenses.models import ExpenseEntry
from apps.activity.time.models import TimeEntry
from apps.agenda.events.models import Event
from apps.agenda.tasks.models import Task
from apps.intakes.models import Intake
from apps.matters.models import Matter
from apps.trust.trust import get_confirmed_client_balance


@login_required
def dash_index(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Upcoming events (next 7 days)
    end_date = today + timedelta(days=7)
    upcoming_events = Event.objects.filter(
        date__gte=today, date__lte=end_date
    ).order_by("date", "party")[:10]

    # Urgent tasks (next 3 days)
    urgent_end_date = today + timedelta(days=2)
    urgent_tasks = Task.objects.filter(
        date_due__gte=today, date_due__lte=urgent_end_date, status="Pending"
    ).order_by("date_due", "priority")[:10]

    # Unbilled hours and fees by user
    unbilled_by_user = (
        TimeEntry.objects.filter(
            entered=0,
            invoice__isnull=True,
        )
        .exclude(comp=1)
        .values("user__username")
        .annotate(
            total_hours=Coalesce(Sum("hours"), 0, output_field=DecimalField()),
            total_fees=Coalesce(
                Sum(F("hours") * F("rate")), 0, output_field=DecimalField()
            ),
        )
        .order_by("user__username")
    )

    # Calculate totals for unbilled
    unbilled_total_hours = sum(entry["total_hours"] for entry in unbilled_by_user)
    unbilled_total_fees = sum(entry["total_fees"] for entry in unbilled_by_user)

    # Matters with low clearance (< $1000)
    # Use subqueries to calculate unbilled amounts
    unbilled_fees_subquery = (
        TimeEntry.objects.filter(
            matter=OuterRef("pk"),
            entered=0,
            invoice__isnull=True,
        )
        .exclude(comp=1)
        .values("matter")
        .annotate(total=Sum(F("hours") * F("rate")))
        .values("total")
    )

    unbilled_expenses_subquery = (
        ExpenseEntry.objects.filter(
            matter=OuterRef("pk"),
            entered=0,
            invoice__isnull=True,
        )
        .exclude(comp=1)
        .values("matter")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    # Get matters with unbilled activity
    matters_with_unbilled = (
        Matter.objects.filter(status="Open")
        .annotate(
            unbilled_fees=Coalesce(
                Subquery(unbilled_fees_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            unbilled_expenses=Coalesce(
                Subquery(unbilled_expenses_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
        )
        .filter(Q(unbilled_fees__gt=0) | Q(unbilled_expenses__gt=0))
    )

    # Convert to list and calculate clearance
    low_clearance_matters = []
    client_trust_balances = {}

    for matter in matters_with_unbilled:
        # Get trust balance for this matter's client (cached by client)
        if matter.client:
            if matter.client.id not in client_trust_balances:
                try:
                    client_trust_balances[matter.client.id] = (
                        get_confirmed_client_balance(matter.client.id)
                    )
                except Exception:
                    client_trust_balances[matter.client.id] = 0

            trust_balance = client_trust_balances[matter.client.id]
            total_activity = matter.unbilled_fees + matter.unbilled_expenses

            # Calculate clearance (only if there's a trust balance)
            if trust_balance > 0:
                clearance = trust_balance - total_activity
                if clearance < 1000:
                    matter.clearance = clearance
                    matter.trust_balance = trust_balance
                    matter.total_activity = total_activity
                    low_clearance_matters.append(matter)

    # Sort by clearance ascending (lowest first)
    low_clearance_matters.sort(key=lambda m: m.clearance)
    low_clearance_matters = low_clearance_matters[:10]

    # Matters with outstanding balance due
    balance_due_matters = []
    all_open_matters = Matter.objects.filter(status="Open")

    for matter in all_open_matters:
        invoice_due = matter.value["invoices"]["due"]
        if invoice_due > 0:
            matter.balance_due = invoice_due
            balance_due_matters.append(matter)

    # Sort by balance due descending (highest first)
    balance_due_matters.sort(key=lambda m: m.balance_due, reverse=True)
    balance_due_matters = balance_due_matters[:10]

    # Open intakes
    open_intakes = Intake.objects.filter(status="Open").order_by("-date")[:10]

    context = {
        "app": "agenda",
        "subapp": "dash",
        "upcoming_events": upcoming_events,
        "urgent_tasks": urgent_tasks,
        "unbilled_by_user": unbilled_by_user,
        "unbilled_total_hours": unbilled_total_hours,
        "unbilled_total_fees": unbilled_total_fees,
        "low_clearance_matters": low_clearance_matters,
        "balance_due_matters": balance_due_matters,
        "open_intakes": open_intakes,
        "today": today,
        "tomorrow": tomorrow,
    }

    return render(request, "agenda/dash/dash.html", context)
