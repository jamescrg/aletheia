from django.db import migrations


def reset_importance(apps, schema_editor):
    """Set all importance values to 3 (Normal)."""
    Note = apps.get_model("notes", "Note")
    Note.objects.exclude(importance=3).update(importance=3)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0013_convert_importance_1_to_5"),
    ]

    operations = [
        migrations.RunPython(reset_importance, noop),
    ]
