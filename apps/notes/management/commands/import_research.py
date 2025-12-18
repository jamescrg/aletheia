"""Import research files as notes."""

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.accounts.models import CustomUser
from apps.notes.models import Note


class Command(BaseCommand):
    help = "Import markdown files from research directory as notes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview without creating notes",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip files that match existing notes by title and topic",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]

        # Get james user
        author = CustomUser.objects.get(username="james")

        # Research directory path
        research_dir = Path("research")

        if not research_dir.exists():
            self.stdout.write(self.style.ERROR("research/ directory not found"))
            return

        created = 0
        skipped = 0

        for file_path in research_dir.rglob("*.md"):
            # Get relative path from research dir
            rel_path = file_path.relative_to(research_dir)

            # Topic is parent folders joined by " - "
            topic = " - ".join(rel_path.parent.parts) if rel_path.parent.parts else ""

            # Title is filename without extension
            title = file_path.stem

            # Check for existing
            if skip_existing:
                if Note.objects.filter(
                    title=title, topic=topic, category="research"
                ).exists():
                    skipped += 1
                    continue

            # Read content
            content = file_path.read_text(encoding="utf-8")

            if dry_run:
                self.stdout.write(f"Would create: {title}")
                self.stdout.write(f"  Topic: {topic or '(none)'}")
            else:
                Note.objects.create(
                    author=author,
                    title=title,
                    content=content,
                    category="research",
                    topic=topic,
                    importance=5,
                    matter=None,
                )
                self.stdout.write(f"Created: {title}")

            created += 1

        action = "Would create" if dry_run else "Created"
        self.stdout.write(self.style.SUCCESS(f"{action} {created} notes"))
        if skipped:
            self.stdout.write(f"Skipped {skipped} existing")
