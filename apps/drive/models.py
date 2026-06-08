from django.db import models
from django.utils import timezone


class DriveSyncState(models.Model):
    """Stores the Google Drive Changes API page token for incremental sync.

    A single row holds the cursor for the case-notes mirror. Mirrors the shape
    of apps.calendar.models.CalendarSyncState (which stores a Calendar sync
    token); here we persist the Drive ``changes`` page token instead.
    """

    page_token = models.TextField(null=True, blank=True)
    # Drive matter-folder names seen during sync with no matching
    # Matter.drive_folder — surfaced as a drift warning on the integrations page.
    unmatched_folders = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_sync_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Drive sync state (token set: {bool(self.page_token)})"

    class Meta:
        db_table = "app_drive_sync_state"
