"""Single source of truth for task status values.

Status is stored on Task as a free-text CharField (no model-level choices), so
these constants are the canonical list used by the filter, the forms, the
per-row status dropdown, and any "active task" queries. Keep new values here.
"""

STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "In progress"
STATUS_ON_HOLD = "On hold"
STATUS_COMPLETE = "Complete"

# Display order (not alphabetical) for choice widgets.
STATUS_CHOICES = (
    (STATUS_PENDING, STATUS_PENDING),
    (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
    (STATUS_ON_HOLD, STATUS_ON_HOLD),
    (STATUS_COMPLETE, STATUS_COMPLETE),
)

# Everything except Complete. This is the default task-list filter and the
# definition of an "active" (not-done) task for digests/reminders/dashboards.
# It's a list because the filter session value is a list and order is preserved.
ACTIVE_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_ON_HOLD]

# Single-select choices for editing one task's status.
FORM_STATUS_CHOICES = STATUS_CHOICES

# Bulk edit adds a "no change" sentinel.
BULK_STATUS_CHOICES = [("", "— No change —"), *STATUS_CHOICES]

# Slugs used in the set-status URL so spaced labels never travel in the path.
STATUS_BY_SLUG = {
    "pending": STATUS_PENDING,
    "in-progress": STATUS_IN_PROGRESS,
    "on-hold": STATUS_ON_HOLD,
    "complete": STATUS_COMPLETE,
}


def coerce_status(value):
    """Normalize a stored status filter value to a list (or None).

    Handles legacy sessions that stored a single string ("Pending") as well as
    the new list form. Returns None when absent so callers can apply their own
    default (typically ACTIVE_STATUSES).
    """
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return [value]
    return list(value)


def status_is_custom(value):
    """True when the selected status set differs from the default active set."""
    return set(coerce_status(value) or ACTIVE_STATUSES) != set(ACTIVE_STATUSES)
