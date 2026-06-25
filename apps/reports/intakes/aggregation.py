"""Intakes report context — shared by the index/list views.

Builds per-month practice-area and status tables plus three chart payloads (a
month-over-month volume bar, a practice-area donut, and an outcomes/conversion
donut) over a rolling 6-month window. The window's end month is held in the
session ("intakes_end") and stepped by the intakes_period view, mirroring the
Revenue / Realization reports.
"""

from collections import defaultdict

from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth

from apps.intakes.models import Intake
from apps.reports.activity.aggregation import _window_months, resolve_end

# Practice areas / statuses to match the intake form choices.
PRACTICE_AREAS = [
    "General",
    "Boundary",
    "Title",
    "LLT - LL",
    "LLT - T",
    "QT",
    "HOA",
    "Fraud",
    "Construction",
]
INTAKE_STATUSES = [
    "Open",
    "Pending",
    "Accepted",
    "Referred Out",
    "Client Declined",
    "Unresponsive",
]
# The status that represents a converted intake (signed client / accepted work).
CONVERTED_STATUS = "Accepted"


def build_intakes_context(request):
    end, current_first = resolve_end(request.session.get("intakes_end"))
    months = _window_months(end)
    window_start = months[0]["date"]
    window_end = months[-1]["date"] + relativedelta(months=1)
    intakes = Intake.objects.filter(date__gte=window_start, date__lt=window_end)

    # --- Per-month practice-area table (contiguous window months) ---
    intake_data = []
    totals_by_practice_area = defaultdict(int)
    for m in months:
        row = {"month": m["date"].strftime("%B %Y"), "practice_areas": {}, "total": 0}
        for pa in PRACTICE_AREAS:
            count = intakes.filter(
                date__year=m["year"], date__month=m["month"], practice_area__name=pa
            ).count()
            row["practice_areas"][pa] = count
            row["total"] += count
            totals_by_practice_area[pa] += count
        row["percentages"] = (
            {
                pa: round(row["practice_areas"][pa] / row["total"] * 100, 1)
                for pa in PRACTICE_AREAS
            }
            if row["total"]
            else {}
        )
        intake_data.append(row)

    total_intakes = sum(r["total"] for r in intake_data)
    percentages_by_practice_area = (
        {
            pa: round(totals_by_practice_area[pa] / total_intakes * 100, 1)
            for pa in PRACTICE_AREAS
        }
        if total_intakes
        else {}
    )

    # --- Per-month status table ---
    status_data = []
    totals_by_status = defaultdict(int)
    for m in months:
        row = {"month": m["date"].strftime("%B %Y"), "statuses": {}, "total": 0}
        for st in INTAKE_STATUSES:
            count = intakes.filter(
                date__year=m["year"], date__month=m["month"], status=st
            ).count()
            row["statuses"][st] = count
            row["total"] += count
            totals_by_status[st] += count
        row["percentages"] = (
            {
                st: round(row["statuses"][st] / row["total"] * 100, 1)
                for st in INTAKE_STATUSES
            }
            if row["total"]
            else {}
        )
        status_data.append(row)

    percentages_by_status = (
        {
            st: round(totals_by_status[st] / total_intakes * 100, 1)
            for st in INTAKE_STATUSES
        }
        if total_intakes
        else {}
    )

    # --- Month-over-month volume bar (0 for empty months) ---
    counts_by_month = {
        (r["m"].year, r["m"].month): r["c"]
        for r in intakes.exclude(date=None)
        .annotate(m=TruncMonth("date"))
        .values("m")
        .annotate(c=Count("id"))
    }
    flow_counts = [counts_by_month.get((m["year"], m["month"]), 0) for m in months]
    flow_chart = {
        "months": [m["name"] for m in months],
        "series": {"flow": [{"label": "Intakes", "count": flow_counts}]},
        "top_labels": [str(c) for c in flow_counts],
    }

    # --- Practice-area distribution donut (no area -> trailing grey "Unspecified") ---
    pa_rows = list(intakes.values("practice_area__name").annotate(c=Count("id")))
    named = sorted(
        (r for r in pa_rows if r["practice_area__name"]), key=lambda r: -r["c"]
    )
    unspecified = sum(r["c"] for r in pa_rows if not r["practice_area__name"])
    pa_labels = [r["practice_area__name"] for r in named]
    pa_counts = [r["c"] for r in named]
    if unspecified:
        pa_labels.append("Unspecified")
        pa_counts.append(unspecified)
    practice_donut = {
        "labels": pa_labels,
        "count": pa_counts,
        "hasOther": bool(unspecified),
    }

    # --- Outcomes / conversion donut ---
    st_counts = {
        r["status"]: r["c"] for r in intakes.values("status").annotate(c=Count("id"))
    }
    conv_labels = [s for s in INTAKE_STATUSES if st_counts.get(s)]
    conv_labels += [s for s in st_counts if s not in INTAKE_STATUSES and st_counts[s]]
    conversion_donut = {
        "labels": conv_labels,
        "count": [st_counts[s] for s in conv_labels],
    }
    total_all = sum(st_counts.values())
    converted_count = st_counts.get(CONVERTED_STATUS, 0)
    conversion_rate = round(converted_count / total_all * 100, 1) if total_all else 0

    return {
        "app": "reports",
        "subapp": "intakes",
        "intake_data": intake_data,
        "status_data": status_data,
        "total_intakes": total_intakes,
        "totals_by_practice_area": dict(totals_by_practice_area),
        "totals_by_status": dict(totals_by_status),
        "percentages_by_practice_area": percentages_by_practice_area,
        "percentages_by_status": percentages_by_status,
        "practice_areas": PRACTICE_AREAS,
        "intake_statuses": INTAKE_STATUSES,
        "flow_chart": flow_chart,
        "practice_donut": practice_donut,
        "conversion_donut": conversion_donut,
        "conversion_rate": conversion_rate,
        "converted_count": converted_count,
        "intakes_total_all": total_all,
        "period_label": end.strftime("%b %Y"),
        "can_go_next": end < current_first,
    }
