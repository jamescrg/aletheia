import pytest

from apps.case.notes.forms import NoteForm

pytestmark = pytest.mark.django_db


class TestNoteForm:
    def test_valid_form(self):
        form = NoteForm(
            data={
                "title": "Test Note",
                "category": "note",
                "date": "2024-01-15",
            }
        )
        assert form.is_valid()

    def test_title_required(self):
        form = NoteForm(
            data={
                "category": "note",
                "date": "2024-01-15",
            }
        )
        assert not form.is_valid()
        assert "title" in form.errors

    def test_category_choices(self):
        """All category choices should be valid."""
        for category_key, _ in [
            ("analysis", "Analysis"),
            ("drafting", "Drafting"),
            ("interview", "Interview"),
            ("issue", "Issue"),
            ("note", "Note"),
        ]:
            form = NoteForm(
                data={
                    "title": "Test",
                    "category": category_key,
                    "date": "2024-01-15",
                }
            )
            assert form.is_valid(), f"Category {category_key} should be valid"

    def test_invalid_category(self):
        form = NoteForm(
            data={
                "title": "Test",
                "category": "invalid_category",
                "date": "2024-01-15",
            }
        )
        assert not form.is_valid()
        assert "category" in form.errors
