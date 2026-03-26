from django.db import migrations, models


def convert_priority(apps, schema_editor):
    """Invert and compress priority from 1-10 scale to 1-5 scale.

    Old: 1 (highest) to 10 (lowest)
    New: 1 (lowest) to 5 (highest)

    Mapping: 1-2→5, 3-4→4, 5-6→3, 7-8→2, 9-10→1
    """
    Task = apps.get_model("tasks", "Task")
    mapping = {1: 5, 2: 5, 3: 4, 4: 4, 5: 3, 6: 3, 7: 2, 8: 2, 9: 1, 10: 1}
    for old_val, new_val in mapping.items():
        Task.objects.filter(priority=old_val).update(priority=new_val)


def reverse_priority(apps, schema_editor):
    """Reverse: expand priority from 1-5 back to 1-10 (using midpoint)."""
    Task = apps.get_model("tasks", "Task")
    mapping = {5: 1, 4: 3, 3: 5, 2: 7, 1: 9}
    for old_val, new_val in mapping.items():
        Task.objects.filter(priority=old_val).update(priority=new_val)


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0006_remove_checklist_models"),
    ]

    operations = [
        migrations.RunPython(convert_priority, reverse_priority),
        migrations.AlterField(
            model_name="task",
            name="priority",
            field=models.IntegerField(default=3),
        ),
    ]
