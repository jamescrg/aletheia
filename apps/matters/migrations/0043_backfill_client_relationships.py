from django.db import migrations


def backfill(apps, schema_editor):
    """Ensure every matter with a client has that client represented as a
    Client-group / Client-role party. Purely additive and idempotent: adds only
    the missing row per matter, never touches the pre-existing Client-role rows
    (co-clients, spouses, clients on FK-less matters)."""
    Matter = apps.get_model("matters", "Matter")
    Group = apps.get_model("matters", "Group")
    Role = apps.get_model("matters", "Role")
    Relationship = apps.get_model("matters", "Relationship")

    client_group = Group.objects.filter(
        is_system=True, name="Client", matter__isnull=True
    ).first()
    client_role = Role.objects.filter(is_system=True, name="Client").first()
    if client_group is None or client_role is None:
        return

    for matter in Matter.objects.filter(client__isnull=False).iterator():
        exists = Relationship.objects.filter(
            matter=matter,
            contact_id=matter.client_id,
            group=client_group,
            role=client_role,
        ).exists()
        if not exists:
            Relationship.objects.create(
                matter=matter,
                contact_id=matter.client_id,
                group=client_group,
                role=client_role,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("matters", "0042_seed_client_system_rows"),
    ]

    # Reverse is a deliberate no-op: the added rows are indistinguishable from
    # legacy Client-role rows, so removing "only what we added" isn't possible
    # without risking real data. The extra rows are harmless valid client
    # parties, so we leave them on reverse rather than delete broadly.
    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
