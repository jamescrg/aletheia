from django.db import migrations


def create_research_topic_folders(apps, schema_editor):
    NoteFolder = apps.get_model("notes", "NoteFolder")
    Note = apps.get_model("notes", "Note")

    research_folder = NoteFolder.objects.filter(name="Research", parent__isnull=True).first()
    if not research_folder:
        return

    research_notes = Note.objects.filter(
        category="research",
        matter__isnull=True,
    ).exclude(topic__isnull=True).exclude(topic="")

    # Cache created folders by their full path tuple
    folder_cache = {}

    for note in research_notes:
        topic = note.topic
        # Strip "Research - " prefix
        if topic.startswith("Research - "):
            topic = topic[len("Research - "):]

        # Split into path parts, e.g. "Civil Procedure - Discovery" -> ["Civil Procedure", "Discovery"]
        parts = [p.strip() for p in topic.split(" - ")]

        # Walk/create folder hierarchy under Research, respecting max depth 3
        # Research is depth 0, so subfolders can be depth 1, 2, 3
        parent = research_folder
        # Limit to 3 levels of subfolders (depth 1, 2, 3)
        parts = parts[:3]

        for i, part in enumerate(parts):
            cache_key = tuple(parts[: i + 1])
            if cache_key in folder_cache:
                parent = folder_cache[cache_key]
                continue

            folder, _ = NoteFolder.objects.get_or_create(
                name=part,
                parent=parent,
                defaults={"depth": parent.depth + 1},
            )
            folder_cache[cache_key] = folder
            parent = folder

        note.folder = parent
        note.save(update_fields=["folder"])


def reverse_research_topic_folders(apps, schema_editor):
    NoteFolder = apps.get_model("notes", "NoteFolder")
    Note = apps.get_model("notes", "Note")

    research_folder = NoteFolder.objects.filter(name="Research", parent__isnull=True).first()
    if not research_folder:
        return

    # Move all notes in research subfolders back to Research
    def get_descendant_ids(folder):
        ids = []
        for child in NoteFolder.objects.filter(parent=folder):
            ids.append(child.pk)
            ids.extend(get_descendant_ids(child))
        return ids

    descendant_ids = get_descendant_ids(research_folder)
    Note.objects.filter(folder_id__in=descendant_ids).update(folder=research_folder)
    NoteFolder.objects.filter(pk__in=descendant_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0011_create_category_folders"),
    ]

    operations = [
        migrations.RunPython(
            create_research_topic_folders,
            reverse_research_topic_folders,
        ),
    ]
