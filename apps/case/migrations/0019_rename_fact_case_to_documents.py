# Generated manually to rename fact.case to fact.documents

from django.db import migrations


def rename_table_if_exists(apps, schema_editor):
    """Rename app_fact_case to app_fact_documents if the old table exists."""
    with schema_editor.connection.cursor() as cursor:
        # Check if the old table exists
        cursor.execute(
            "SELECT EXISTS(SELECT FROM pg_tables WHERE tablename = 'app_fact_case')"
        )
        old_table_exists = cursor.fetchone()[0]

        if old_table_exists:
            cursor.execute(
                'ALTER TABLE "app_fact_case" RENAME TO "app_fact_documents"'
            )


def reverse_rename(apps, schema_editor):
    """Reverse: rename app_fact_documents back to app_fact_case."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS(SELECT FROM pg_tables WHERE tablename = 'app_fact_documents')"
        )
        new_table_exists = cursor.fetchone()[0]

        if new_table_exists:
            cursor.execute(
                'ALTER TABLE "app_fact_documents" RENAME TO "app_fact_case"'
            )


class Migration(migrations.Migration):
    """
    Rename the 'case' ManyToManyField on Fact to 'documents'.
    This was renamed during the documents->case app refactor.

    Uses RunPython to conditionally rename the table only if it has the old name.
    Uses SeparateDatabaseAndState to update Django's state regardless.
    """

    dependencies = [
        ("case", "0018_change_paragraph_number_to_char"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(rename_table_if_exists, reverse_rename),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="fact",
                    old_name="case",
                    new_name="documents",
                ),
            ],
        ),
    ]
