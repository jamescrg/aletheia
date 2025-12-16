"""
Management command to copy all Outlines to Notes.

Converts OutlineItems to markdown content with inline reference chips.
"""

from django.core.management.base import BaseCommand

from apps.case.models import Note
from apps.outlines.models import Outline


class Command(BaseCommand):
    help = "Copy all Outlines to Notes, converting items to markdown content"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be created without actually creating notes",
        )
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete all existing notes before copying",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip outlines that match existing notes by date and title",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delete_existing = options["delete_existing"]
        skip_existing = options["skip_existing"]

        if delete_existing and skip_existing:
            self.stdout.write(
                self.style.ERROR(
                    "Cannot use both --delete-existing and --skip-existing"
                )
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            self.stdout.write("")

        # Handle deletion of existing notes
        if delete_existing:
            existing_count = Note.objects.count()
            if dry_run:
                self.stdout.write(f"Would delete {existing_count} existing notes")
                self.stdout.write("")
            else:
                Note.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f"Deleted {existing_count} existing notes")
                )

        outlines = Outline.objects.all().select_related("user", "matter")

        created_count = 0
        skipped_count = 0

        for outline in outlines:
            # Check for existing note if skip_existing is enabled
            if skip_existing:
                exists = Note.objects.filter(
                    matter=outline.matter,
                    title=outline.title,
                    date=outline.date,
                ).exists()
                if exists:
                    if dry_run:
                        self.stdout.write(
                            f"Would skip (exists): {outline.title} ({outline.date})"
                        )
                    else:
                        self.stdout.write(
                            f"Skipped (exists): {outline.title} ({outline.date})"
                        )
                    skipped_count += 1
                    continue

            content = self.convert_items_to_markdown(outline)

            if dry_run:
                self.stdout.write(f"Would create note: {outline.title}")
                self.stdout.write(f"  Matter: {outline.matter.name}")
                self.stdout.write(f"  Date: {outline.date}")
                self.stdout.write(f"  User: {outline.user}")
                self.stdout.write(f"  Category: {outline.category}")
                self.stdout.write("  Content preview:")
                # Show first few lines of content
                lines = content.split("\n")[:5]
                for line in lines:
                    self.stdout.write(f"    {line}")
                if len(content.split("\n")) > 5:
                    self.stdout.write(
                        f"    ... ({len(content.split(chr(10)))} lines total)"
                    )
                self.stdout.write("")
            else:
                note = Note.objects.create(
                    user=outline.user,
                    matter=outline.matter,
                    title=outline.title,
                    date=outline.date,
                    category=outline.category,
                    importance=outline.importance,
                    content=content,
                )
                self.stdout.write(f"Created note: {note.title} (ID: {note.id})")

            created_count += 1

        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Would create {created_count} notes"))
            if skipped_count:
                self.stdout.write(f"Would skip {skipped_count} existing notes")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created {created_count} notes")
            )
            if skipped_count:
                self.stdout.write(f"Skipped {skipped_count} existing notes")

    def convert_items_to_markdown(self, outline):
        """Convert outline items to markdown content."""
        lines = []
        root_items = outline.get_root_items().prefetch_related(
            "documents", "highlights"
        )

        for item in root_items:
            self._process_item(item, lines)

        return "\n".join(lines)

    def _process_item(self, item, lines):
        """Recursively process an item and its children."""
        depth = item.get_depth()

        # Build reference string
        refs = []
        for doc in item.documents.all():
            refs.append(f"[[doc:{doc.id}|{doc.citation}]]")
        for hl in item.highlights.all():
            refs.append(f"[[hl:{hl.id}|{hl.citation}]]")
        ref_str = " ".join(refs)

        # Format line based on heading flag
        content = item.content or ""
        if item.heading:
            line = f"## {content}"
            if ref_str:
                line += f" {ref_str}"
        else:
            indent = "  " * depth
            line = f"{indent}- {content}"
            if ref_str:
                line += f" {ref_str}"

        lines.append(line)

        # Process children recursively
        children = item.get_children().prefetch_related("documents", "highlights")
        for child in children:
            self._process_item(child, lines)
