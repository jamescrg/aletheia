from django.db import migrations


def seed(apps, schema_editor):
    """Mark the firm-wide Client group and the Client role as protected system
    rows (the matter-client mirror relationship depends on them). The Client group
    already exists from 0015; the Client role is not seeded anywhere, so create it
    if missing. Idempotent."""
    Group = apps.get_model("matters", "Group")
    Role = apps.get_model("matters", "Role")

    group = Group.objects.filter(name="Client", matter__isnull=True).first()
    if group is None:
        group = Group.objects.create(name="Client", order=1, matter=None)
    if not group.is_system:
        group.is_system = True
        group.save(update_fields=["is_system"])

    role = Role.objects.filter(name="Client").first()
    if role is None:
        role = Role.objects.create(name="Client")
    if not role.is_system:
        role.is_system = True
        role.save(update_fields=["is_system"])


def unseed(apps, schema_editor):
    Group = apps.get_model("matters", "Group")
    Role = apps.get_model("matters", "Role")
    Group.objects.filter(is_system=True, name="Client").update(is_system=False)
    Role.objects.filter(is_system=True, name="Client").update(is_system=False)


class Migration(migrations.Migration):
    dependencies = [
        ("matters", "0041_group_is_system_historicalgroup_is_system_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
