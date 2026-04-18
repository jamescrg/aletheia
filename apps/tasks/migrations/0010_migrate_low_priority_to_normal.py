"""Migrate tasks with priority 1-3 to Normal (4) after expanding to 7-level scale."""

from django.db import migrations


def migrate_low_to_normal(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    Task.objects.filter(priority__lte=3).update(priority=4)


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0009_priority_7_levels"),
    ]

    operations = [
        migrations.RunPython(migrate_low_to_normal, migrations.RunPython.noop),
    ]
