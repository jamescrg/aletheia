from django.db import migrations


def reset_ai_context(apps, schema_editor):
    """Set all ai_context values to 'auto' across all models."""
    for model_name in ("Document", "CaseLaw", "Conversation"):
        Model = apps.get_model("case", model_name)
        Model.objects.exclude(ai_context="auto").update(ai_context="auto")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("case", "0053_remove_conversation_is_reference"),
    ]

    operations = [
        migrations.RunPython(reset_ai_context, noop),
    ]
