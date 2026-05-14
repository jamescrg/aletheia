from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoicing", "0016_matter_cascade"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="show_comp",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="historicalinvoice",
            name="show_comp",
            field=models.BooleanField(default=True),
        ),
    ]
