"""One-time fix for documents whose files were relocated to the deprecated
name-based storage layout (documents/{matter_name}_{id}/{category}/.../{file})
by the old Matter.save() rename logic. The current convention is ID-based
(documents/{matter_id}/{document_id}.ext, see case.models.document_upload_path).

Scoped to the matters known to be affected. Idempotent and guarded: a document
already on the ID-based path is skipped, and files are only moved when they
actually exist at the current path (so it's a safe no-op in environments without
the media, e.g. the dev server).
"""

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage as storage
from django.db import migrations

# Sklar Emerson (1034), CB Moskowitz (1035)
AFFECTED_MATTER_IDS = [1034, 1035]


def fix_document_paths(apps, schema_editor):
    Document = apps.get_model("case", "Document")

    fixed = 0
    for doc in Document.objects.filter(matter_id__in=AFFECTED_MATTER_IDS):
        current = doc.file.name if doc.file else ""
        if not current:
            continue

        ext = current.rsplit(".", 1)[-1].lower() if "." in current else "pdf"
        expected = f"documents/{doc.matter_id}/{doc.pk}.{ext}"
        if current == expected:
            continue  # already on the ID-based scheme

        if storage.exists(current) and not storage.exists(expected):
            # Physically move the file back to the ID-based path.
            with storage.open(current, "rb") as f:
                data = f.read()
            storage.save(expected, ContentFile(data))
            storage.delete(current)
            Document.objects.filter(pk=doc.pk).update(file=expected)
            fixed += 1
        elif storage.exists(expected):
            # File is already in the right place; just correct the DB pointer.
            Document.objects.filter(pk=doc.pk).update(file=expected)
            fixed += 1
        # else: file missing from this environment's storage — leave as-is.

    if fixed:
        print(f"  fixed {fixed} document path(s) for matters {AFFECTED_MATTER_IDS}")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("case", "0067_alter_conversation_llm_and_more"),
    ]

    operations = [
        migrations.RunPython(fix_document_paths, noop),
    ]
