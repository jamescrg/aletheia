"""Fix document records that use the old upload path format.

Old format: documents/{matter_name}_{id}/{category}/{filename}.pdf
New format: documents/{matter_id}/{document_id}.pdf

Checks whether the file exists at the corrected path before updating.
"""

from django.core.management.base import BaseCommand

from apps.case.models import Document


class Command(BaseCommand):
    help = "Fix document file paths from old naming format to current convention"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without updating",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        fixed = 0
        missing = 0

        for doc in Document.objects.all().order_by("id"):
            if not doc.file:
                continue

            path = doc.file.name
            expected_ext = path.rsplit(".", 1)[-1].lower() if "." in path else "pdf"
            expected_path = f"documents/{doc.matter_id}/{doc.pk}.{expected_ext}"

            if path == expected_path:
                continue

            # Path doesn't match convention — check if file exists at the correct path
            storage = doc.file.storage
            exists_at_correct = storage.exists(expected_path)
            exists_at_current = storage.exists(path)

            if exists_at_correct:
                self.stdout.write(f"  FIX  ID={doc.id}  {path}  ->  {expected_path}")
                if not dry_run:
                    Document.objects.filter(id=doc.id).update(file=expected_path)
                fixed += 1
            elif exists_at_current:
                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIP  ID={doc.id}  file exists at non-standard path: {path}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  MISSING  ID={doc.id}  not found at {path} or {expected_path}"
                    )
                )
                missing += 1

        self.stdout.write("")
        if fixed:
            action = "Would fix" if dry_run else "Fixed"
            self.stdout.write(self.style.SUCCESS(f"{action} {fixed} document path(s)."))
        if missing:
            self.stdout.write(
                self.style.ERROR(
                    f"{missing} document(s) missing from storage entirely."
                )
            )
        if not fixed and not missing:
            self.stdout.write(self.style.SUCCESS("All document paths are correct."))
