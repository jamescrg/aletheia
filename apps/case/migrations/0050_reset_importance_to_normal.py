from django.db import migrations


def reset_importance(apps, schema_editor):
    """Set all importance values to 3 (Normal)."""
    for model_name in ("Document", "Highlight", "Fact", "Witness", "CaseLaw"):
        Model = apps.get_model("case", model_name)
        Model.objects.exclude(importance=3).update(importance=3)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("case", "0049_convert_importance_1_to_5"),
    ]

    operations = [
        migrations.RunPython(reset_importance, noop),
    ]
