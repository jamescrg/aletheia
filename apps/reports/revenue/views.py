from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from apps.invoicing.payments.models import Payment
from apps.management.filter_manager import FilterManager

from .filters import RevenueReportFilter


@login_required
@staff_member_required
def revenue_index(request):
    # Get filter data from session
    filter_data = request.session.get("revenue_filter", {})

    # Set date filter objects (None means no date filtering)
    date_from_obj = None
    date_to_obj = None
    date_from = filter_data.get("date_from")
    date_to = filter_data.get("date_to")

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None

    # Calculate months based on filter or default to last 6 months
    today = date.today()
    months = []

    if date_from_obj and date_to_obj:
        # Use filtered date range
        current_date = date_from_obj.replace(day=1)  # Start at beginning of month
        end_date = date_to_obj

        while current_date <= end_date:
            months.append(
                {
                    "date": current_date,
                    "name": current_date.strftime("%B %Y"),
                    "year": current_date.year,
                    "month": current_date.month,
                }
            )
            current_date = current_date + relativedelta(months=1)
    elif date_from_obj:
        # From date_from to today
        current_date = date_from_obj.replace(day=1)

        while current_date <= today:
            months.append(
                {
                    "date": current_date,
                    "name": current_date.strftime("%B %Y"),
                    "year": current_date.year,
                    "month": current_date.month,
                }
            )
            current_date = current_date + relativedelta(months=1)
    elif date_to_obj:
        # Last 6 months up to date_to
        for i in range(5, -1, -1):
            month_date = date_to_obj - relativedelta(months=i)
            if month_date <= date_to_obj:
                months.append(
                    {
                        "date": month_date,
                        "name": month_date.strftime("%B %Y"),
                        "year": month_date.year,
                        "month": month_date.month,
                    }
                )
    else:
        # Default: last 3 months
        for i in range(2, -1, -1):
            month_date = today - relativedelta(months=i)
            months.append(
                {
                    "date": month_date,
                    "name": month_date.strftime("%B %Y"),
                    "year": month_date.year,
                    "month": month_date.month,
                }
            )
        date_from_obj = (today - relativedelta(months=2)).replace(day=1)
        date_from = date_from_obj.strftime("%Y-%m-%d")

    # Build revenue data for each month
    revenue_data = []
    total_revenue = 0

    for month_info in months:
        # Get payments for this month
        payments = Payment.objects.filter(
            date__year=month_info["year"], date__month=month_info["month"]
        )

        # Apply additional date filtering if specified
        if date_from_obj:
            payments = payments.filter(date__gte=date_from_obj)
        if date_to_obj:
            payments = payments.filter(date__lte=date_to_obj)

        month_revenue = payments.aggregate(Sum("amount"))["amount__sum"] or 0
        total_revenue += month_revenue

        revenue_data.append(
            {
                "name": month_info["name"],
                "revenue": month_revenue,
                "payments_count": payments.count(),
            }
        )

    # Calculate averages
    num_months = len(months) if months else 1  # Avoid division by zero
    average_revenue = total_revenue / num_months

    context = {
        "app": "reports",
        "subapp": "revenue",
        "revenue_data": revenue_data,
        "total_revenue": total_revenue,
        "average_revenue": average_revenue,
        "months": [m["name"] for m in months],
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "reports/revenue/main.html", context)


@login_required
@staff_member_required
def revenue_list(request):
    # Get filter data from session
    filter_data = request.session.get("revenue_filter", {})

    # Set date filter objects (None means no date filtering)
    date_from_obj = None
    date_to_obj = None
    date_from = filter_data.get("date_from")
    date_to = filter_data.get("date_to")

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None

    # Calculate months based on filter or default to last 6 months
    today = date.today()
    months = []

    if date_from_obj and date_to_obj:
        # Use filtered date range
        current_date = date_from_obj.replace(day=1)  # Start at beginning of month
        end_date = date_to_obj

        while current_date <= end_date:
            months.append(
                {
                    "date": current_date,
                    "name": current_date.strftime("%B %Y"),
                    "year": current_date.year,
                    "month": current_date.month,
                }
            )
            current_date = current_date + relativedelta(months=1)
    elif date_from_obj:
        # From date_from to today
        current_date = date_from_obj.replace(day=1)

        while current_date <= today:
            months.append(
                {
                    "date": current_date,
                    "name": current_date.strftime("%B %Y"),
                    "year": current_date.year,
                    "month": current_date.month,
                }
            )
            current_date = current_date + relativedelta(months=1)
    elif date_to_obj:
        # Last 6 months up to date_to
        for i in range(5, -1, -1):
            month_date = date_to_obj - relativedelta(months=i)
            if month_date <= date_to_obj:
                months.append(
                    {
                        "date": month_date,
                        "name": month_date.strftime("%B %Y"),
                        "year": month_date.year,
                        "month": month_date.month,
                    }
                )
    else:
        # Default: last 3 months
        for i in range(2, -1, -1):
            month_date = today - relativedelta(months=i)
            months.append(
                {
                    "date": month_date,
                    "name": month_date.strftime("%B %Y"),
                    "year": month_date.year,
                    "month": month_date.month,
                }
            )
        date_from_obj = (today - relativedelta(months=2)).replace(day=1)
        date_from = date_from_obj.strftime("%Y-%m-%d")

    # Build revenue data for each month
    revenue_data = []
    total_revenue = 0

    for month_info in months:
        # Get payments for this month
        payments = Payment.objects.filter(
            date__year=month_info["year"], date__month=month_info["month"]
        )

        # Apply additional date filtering if specified
        if date_from_obj:
            payments = payments.filter(date__gte=date_from_obj)
        if date_to_obj:
            payments = payments.filter(date__lte=date_to_obj)

        month_revenue = payments.aggregate(Sum("amount"))["amount__sum"] or 0
        total_revenue += month_revenue

        revenue_data.append(
            {
                "name": month_info["name"],
                "revenue": month_revenue,
                "payments_count": payments.count(),
            }
        )

    # Calculate averages
    num_months = len(months) if months else 1  # Avoid division by zero
    average_revenue = total_revenue / num_months

    context = {
        "app": "reports",
        "subapp": "revenue",
        "revenue_data": revenue_data,
        "total_revenue": total_revenue,
        "average_revenue": average_revenue,
        "months": [m["name"] for m in months],
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "reports/revenue/list.html", context)


@login_required
@staff_member_required
def revenue_filter(request):
    filter_manager = FilterManager(request, RevenueReportFilter, "revenue_filter")

    if filter_manager.process_filter():
        return HttpResponse(status=204, headers={"HX-Trigger": "revenueChanged"})

    # Get current filter data from session for display
    filter_data = request.session.get("revenue_filter", {})

    return render(request, "reports/revenue/filter.html", {"filter_data": filter_data})
