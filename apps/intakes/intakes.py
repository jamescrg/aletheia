from apps.intakes.filter_intakes import IntakeFilter
from apps.intakes.models import Note, UserIntakeView
from apps.management.pagination import CustomPaginator


def get_table_data(request):
    table_data = {}

    default_filter = {"status": "Open", "order_by": "-date"}

    filter_data = request.session.get("intake_filter", {})

    if filter_data:
        filter = IntakeFilter(filter_data)
        intakes = filter.qs
    else:
        filter = IntakeFilter(default_filter)
        intakes = filter.qs

    request.session["intake_filter"] = filter.data
    request.session.modified = True

    number_intakes = intakes.count()

    pagination = CustomPaginator(
        intakes, per_page=10, request=request, session_key="intake_pagination"
    )

    # Get user's view history for badge notification system
    user_views = UserIntakeView.objects.filter(user=request.user).values(
        "intake_id", "last_viewed_at"
    )
    view_times = {v["intake_id"]: v["last_viewed_at"] for v in user_views}

    # Check each intake for new notes
    intake_list = pagination.get_object_list()
    for intake in intake_list:
        # Only check for badges on open intakes
        if intake.status == "Open":
            last_viewed = view_times.get(intake.id)
            if last_viewed:
                # Check if there are notes created after last view
                intake.has_new_notes = Note.objects.filter(
                    intake=intake, date__gt=last_viewed.date()
                ).exists()
            else:
                # Never viewed - always show badge
                intake.has_new_notes = True
        else:
            intake.has_new_notes = False

    table_data = {
        "pagination": pagination,
        "intakes": intake_list,
        "session_key": "intake_pagination",
        "trigger_key": "intakesChanged",
        "number_intakes": number_intakes,
        "filter_label": filter_data.get("filter_label", None) if filter_data else None,
    }

    return table_data
