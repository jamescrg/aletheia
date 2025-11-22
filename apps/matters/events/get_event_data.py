from datetime import date, datetime, timedelta

from apps.agenda.events.models import Event
from apps.matters.proceedings.models import Proceeding


def get_event_data(matter):
    proceeding = Proceeding.objects.filter(matter=matter.id, primary=True).first()
    pending_events = Event.objects.filter(matter=matter, status="Pending").order_by(
        "date"
    )

    third_day = date.today() + timedelta(days=3)
    past_events = (
        Event.objects.filter(matter=matter).exclude(status="Pending").order_by("-date")
    )

    # Calculate duration for pending events
    for event in pending_events:
        if event.start_time and event.end_time:
            start = datetime.combine(datetime.today(), event.start_time)
            end = datetime.combine(datetime.today(), event.end_time)
            duration_delta = end - start
            event.duration = duration_delta.total_seconds() / 3600
        else:
            event.duration = None

    # Calculate duration for past events
    for event in past_events:
        if event.start_time and event.end_time:
            start = datetime.combine(datetime.today(), event.start_time)
            end = datetime.combine(datetime.today(), event.end_time)
            duration_delta = end - start
            event.duration = duration_delta.total_seconds() / 3600
        else:
            event.duration = None

    event_data = {
        "matter": matter,
        "proceeding": proceeding,
        "pending_events": pending_events,
        "past_events": past_events,
        "third_day": third_day,
    }

    return event_data
