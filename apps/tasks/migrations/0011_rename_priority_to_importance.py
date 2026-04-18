"""Rename priority field to importance on Task and HistoricalTask."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0010_migrate_low_priority_to_normal"),
    ]

    operations = [
        migrations.RenameField(
            model_name="task",
            old_name="priority",
            new_name="importance",
        ),
        migrations.RenameField(
            model_name="historicaltask",
            old_name="priority",
            new_name="importance",
        ),
    ]
