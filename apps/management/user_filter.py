from apps.accounts.models import CustomUser


def cycle_user_filter(request, session_key, direction):
    """Advance a tab's user filter to the next/previous active user.

    Shared by the tasks/time/expenses "cycle user" keyboard shortcut (u / U).
    The cycle includes an "All users" stop (no user filter), so tapping the key
    walks All -> first user -> ... -> last user -> All and wraps around.

    `session_key` is the tab's filter dict key ("tasks_filter", "time_filter",
    "expenses_filter"); `direction` is "next" or "prev" (anything but "prev"
    counts as next). Mutates request.session[session_key]["user"] in place.
    """
    user_ids = list(
        CustomUser.objects.filter(is_active=True)
        .order_by("username")
        .values_list("id", flat=True)
    )
    # None is the "All users" stop (the user key absent from the filter).
    stops = [None, *user_ids]

    filter_data = dict(request.session.get(session_key, {}))
    current = filter_data.get("user")
    current = int(current) if current not in (None, "", 0, "0") else None
    try:
        idx = stops.index(current)
    except ValueError:
        idx = 0

    step = -1 if direction == "prev" else 1
    new_user = stops[(idx + step) % len(stops)]

    if new_user is None:
        filter_data.pop("user", None)
    else:
        filter_data["user"] = new_user

    request.session[session_key] = filter_data
    request.session.modified = True
