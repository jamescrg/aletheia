"""Backfill Payment.client / Credit.client from matter.client.

Step 2 of the matter -> client refactor. Runs after the nullable `client` field
is added (0024) and before it's made non-null and `matter` is dropped (later).
Rows whose matter has no client can't be backfilled; they're reported, not
guessed at, so they can be cleaned up before the non-null migration.
"""

from django.db import migrations


def backfill_client(apps, schema_editor):
    for label in ("Payment", "Credit"):
        model = apps.get_model("invoicing", label)
        to_update = []
        orphans = []
        qs = model.objects.filter(client__isnull=True).select_related("matter")
        for obj in qs.iterator():
            client_id = getattr(obj.matter, "client_id", None)
            if client_id:
                obj.client_id = client_id
                to_update.append(obj)
            else:
                orphans.append(obj.pk)
        model.objects.bulk_update(to_update, ["client"], batch_size=500)
        print(
            f"  {label}: backfilled {len(to_update)}; "
            f"orphans (matter has no client): {len(orphans)} {orphans[:20]}"
        )


def reverse(apps, schema_editor):
    # Non-destructive: the forward pass only fills a value derivable from
    # matter.client, so reverse is a no-op.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("invoicing", "0024_add_client_to_payment_credit"),
    ]

    operations = [
        migrations.RunPython(backfill_client, reverse),
    ]
