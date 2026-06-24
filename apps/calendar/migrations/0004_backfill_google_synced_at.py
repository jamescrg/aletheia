from django.db import migrations
from django.db.models import F


def mark_existing_synced(apps, schema_editor):
    """Events that already have a google_id are, as of now, in sync with Google.
    Stamp google_synced_at = updated_at so the new reconcile() doesn't re-push
    every one of them on its first run. Events without a google_id keep
    google_synced_at = NULL and are correctly treated as the never-synced
    backlog to adopt on (re)connect."""
    Event = apps.get_model("calendar", "Event")
    Event.objects.exclude(google_id__isnull=True).exclude(google_id="").update(
        google_synced_at=F("updated_at")
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("calendar", "0003_pendinggoogledeletion_event_google_synced_at_and_more"),
    ]

    operations = [
        migrations.RunPython(mark_existing_synced, noop),
    ]
