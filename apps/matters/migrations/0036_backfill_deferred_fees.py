from django.db import migrations


def set_deferred_fees(apps, schema_editor):
    """Bootstrap the flag: any matter that already has a DEFERRED invoice is, by
    definition, on a deferred-fee arrangement."""
    Matter = apps.get_model("matters", "Matter")
    Invoice = apps.get_model("invoicing", "Invoice")

    matter_ids = (
        Invoice.objects.filter(status="DEFERRED")
        .values_list("matter_id", flat=True)
        .distinct()
    )
    Matter.objects.filter(id__in=list(matter_ids)).update(deferred_fees=True)


def unset_deferred_fees(apps, schema_editor):
    Matter = apps.get_model("matters", "Matter")
    Matter.objects.update(deferred_fees=False)


class Migration(migrations.Migration):
    dependencies = [
        ("matters", "0035_historicalmatter_deferred_fees_matter_deferred_fees"),
        ("invoicing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(set_deferred_fees, unset_deferred_fees),
    ]
