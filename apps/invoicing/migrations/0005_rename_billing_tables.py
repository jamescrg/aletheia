# Manual migration to rename billing tables to invoicing tables

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("invoicing", "0004_alter_credit_date"),
    ]

    operations = [
        # Rename tables
        migrations.RunSQL(
            "ALTER TABLE app_billing_invoice RENAME TO app_invoicing_invoice;",
            reverse_sql="ALTER TABLE app_invoicing_invoice RENAME TO app_billing_invoice;",
        ),
        migrations.RunSQL(
            "ALTER TABLE app_billing_payment RENAME TO app_invoicing_payment;",
            reverse_sql="ALTER TABLE app_invoicing_payment RENAME TO app_billing_payment;",
        ),
        migrations.RunSQL(
            "ALTER TABLE app_billing_credit RENAME TO app_invoicing_credit;",
            reverse_sql="ALTER TABLE app_invoicing_credit RENAME TO app_billing_credit;",
        ),
        # Rename indexes
        migrations.RunSQL(
            "ALTER INDEX app_billing_matter__ead650_idx RENAME TO app_invoicing_matter__ead650_idx;",
            reverse_sql="ALTER INDEX app_invoicing_matter__ead650_idx RENAME TO app_billing_matter__ead650_idx;",
        ),
        migrations.RunSQL(
            "ALTER INDEX app_billing_matter__f043b6_idx RENAME TO app_invoicing_matter__f043b6_idx;",
            reverse_sql="ALTER INDEX app_invoicing_matter__f043b6_idx RENAME TO app_billing_matter__f043b6_idx;",
        ),
        migrations.RunSQL(
            "ALTER INDEX app_billing_matter__17a947_idx RENAME TO app_invoicing_matter__17a947_idx;",
            reverse_sql="ALTER INDEX app_invoicing_matter__17a947_idx RENAME TO app_billing_matter__17a947_idx;",
        ),
    ]