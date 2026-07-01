from django.db import migrations
from django.db.models import F

# Keep in sync with Group.MATTER_CATEGORY_ORDER_BASE.
BASE = 1000


def rebase_up(apps, schema_editor):
    """Move existing matter-specific categories into the high order band so they
    sort after the firm-wide groups. Each matter's relative order is preserved."""
    Group = apps.get_model("matters", "Group")
    Group.objects.filter(matter__isnull=False, order__lt=BASE).update(
        order=F("order") + BASE
    )


def rebase_down(apps, schema_editor):
    Group = apps.get_model("matters", "Group")
    Group.objects.filter(matter__isnull=False, order__gte=BASE).update(
        order=F("order") - BASE
    )


class Migration(migrations.Migration):
    dependencies = [
        ("matters", "0038_group_matter_historicalgroup_matter"),
    ]

    operations = [
        migrations.RunPython(rebase_up, rebase_down),
    ]
